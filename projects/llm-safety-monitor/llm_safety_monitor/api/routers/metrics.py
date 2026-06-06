from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from llm_safety_monitor.api.database import get_db
from llm_safety_monitor.api.models import ClassificationResult, Interaction
from llm_safety_monitor.api.schemas import (
    CalibrationBin,
    CalibrationResponse,
    DisagreementSample,
    DisagreementsResponse,
    MetricsResponse,
    ModelCalibration,
    ModelMetrics,
)

router = APIRouter(prefix="/metrics", tags=["metrics"])

_N_BINS = 10


@router.get("", response_model=MetricsResponse)
async def get_metrics(db: AsyncSession = Depends(get_db)) -> MetricsResponse:
    """Per-model F1, precision, recall computed against live-stream ground truth."""
    result = await db.execute(
        select(
            ClassificationResult.model_name,
            ClassificationResult.predicted_label,
            Interaction.ground_truth_safe,
        )
        .join(Interaction, ClassificationResult.event_id == Interaction.id)
        .where(Interaction.ground_truth_safe.is_not(None))
    )
    rows = result.all()

    by_model: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for model_name, predicted_label, ground_truth_safe in rows:
        y_true = 0 if ground_truth_safe else 1
        by_model[model_name].append((predicted_label, y_true))

    models: list[ModelMetrics] = []
    for model_name, pairs in sorted(by_model.items()):
        f1, precision, recall = _compute_metrics(pairs)
        models.append(
            ModelMetrics(
                model_name=model_name,
                f1=f1,
                precision=precision,
                recall=recall,
                sample_count=len(pairs),
            )
        )

    return MetricsResponse(models=models)


@router.get("/calibration", response_model=CalibrationResponse)
async def get_calibration(db: AsyncSession = Depends(get_db)) -> CalibrationResponse:
    """Per-model calibration data for reliability diagrams."""
    result = await db.execute(
        select(
            ClassificationResult.model_name,
            ClassificationResult.confidence,
            Interaction.ground_truth_safe,
        )
        .join(Interaction, ClassificationResult.event_id == Interaction.id)
        .where(Interaction.ground_truth_safe.is_not(None))
    )
    rows = result.all()

    by_model: dict[str, list[tuple[float, int]]] = defaultdict(list)
    for model_name, confidence, ground_truth_safe in rows:
        y_true = 0 if ground_truth_safe else 1
        by_model[model_name].append((confidence, y_true))

    models: list[ModelCalibration] = []
    for model_name, pairs in sorted(by_model.items()):
        bins = _compute_calibration_bins(pairs)
        models.append(ModelCalibration(model_name=model_name, bins=bins))

    return CalibrationResponse(models=models)


@router.get("/disagreements", response_model=DisagreementsResponse)
async def get_disagreements(db: AsyncSession = Depends(get_db)) -> DisagreementsResponse:
    """Events where pair classifier and taxonomy classifier contradict each other."""
    PairClf = aliased(ClassificationResult, name="pair_c")
    TaxClf = aliased(ClassificationResult, name="tax_c")

    result = await db.execute(
        select(Interaction, PairClf, TaxClf)
        .join(PairClf, (PairClf.event_id == Interaction.id) & (PairClf.model_name == "pair_classifier"))
        .join(TaxClf, (TaxClf.event_id == Interaction.id) & (TaxClf.model_name == "taxonomy_classifier"))
        .order_by(Interaction.created_at.desc())
        .limit(200)
    )
    rows = result.all()

    samples: list[DisagreementSample] = []
    for interaction, pair_clf, tax_clf in rows:
        tax_labels: list[str] = tax_clf.taxonomy_labels or []
        pair_label: int = pair_clf.predicted_label
        # Disagreement: pair says safe but taxonomy flags categories, or vice versa
        is_disagreement = (pair_label == 0 and len(tax_labels) > 0) or (
            pair_label == 1 and len(tax_labels) == 0
        )
        if is_disagreement:
            samples.append(
                DisagreementSample(
                    event_id=interaction.id,
                    prompt_text=(interaction.prompt_text or "")[:200],
                    pair_label=pair_label,
                    taxonomy_labels=tax_labels,
                )
            )

    return DisagreementsResponse(total=len(samples), samples=samples[:50])


def _compute_metrics(pairs: list[tuple[int, int]]) -> tuple[float, float, float]:
    tp = sum(1 for p, a in pairs if p == 1 and a == 1)
    fp = sum(1 for p, a in pairs if p == 1 and a == 0)
    fn = sum(1 for p, a in pairs if p == 0 and a == 1)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return round(f1, 4), round(precision, 4), round(recall, 4)


def _compute_calibration_bins(pairs: list[tuple[float, int]]) -> list[CalibrationBin]:
    bin_size = 1.0 / _N_BINS
    bins: list[CalibrationBin] = []
    for i in range(_N_BINS):
        lower = i * bin_size
        upper = (i + 1) * bin_size
        in_bin = [
            a
            for c, a in pairs
            if lower <= c < upper or (i == _N_BINS - 1 and c == 1.0)
        ]
        if not in_bin:
            continue
        bins.append(
            CalibrationBin(
                bin_lower=round(lower, 2),
                bin_upper=round(upper, 2),
                count=len(in_bin),
                actual_positive_rate=round(sum(in_bin) / len(in_bin), 4),
            )
        )
    return bins
