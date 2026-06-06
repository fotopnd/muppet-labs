from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from llm_safety_monitor.api.database import get_db
from llm_safety_monitor.api.models import ClassificationResult, Interaction
from llm_safety_monitor.api.schemas import (
    CalibrationBin,
    CalibrationResponse,
    DisagreementSample,
    DisagreementsResponse,
    MetricPoint,
    MetricsResponse,
    ModelCalibration,
    ModelMetrics,
    ModelTimeseries,
    TaxonomyBucket,
    TaxonomyTimeseriesResponse,
    TimeseriesResponse,
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


_DISAGREEMENT_WHERE = """
    (pair_c.predicted_label = 0 AND tax_c.taxonomy_labels != '[]' AND tax_c.taxonomy_labels IS NOT NULL)
    OR
    (pair_c.predicted_label = 1 AND (tax_c.taxonomy_labels IS NULL OR tax_c.taxonomy_labels = '[]'))
"""


@router.get("/disagreements", response_model=DisagreementsResponse)
async def get_disagreements(db: AsyncSession = Depends(get_db)) -> DisagreementsResponse:
    """Events where pair classifier and taxonomy classifier contradict each other."""
    rows = (
        await db.execute(
            text(f"""
                SELECT i.id, i.prompt_text, pair_c.predicted_label, tax_c.taxonomy_labels
                FROM interactions i
                JOIN classifications pair_c
                    ON pair_c.event_id = i.id AND pair_c.model_name = 'pair_classifier'
                JOIN classifications tax_c
                    ON tax_c.event_id = i.id AND tax_c.model_name = 'taxonomy_classifier'
                WHERE {_DISAGREEMENT_WHERE}
                ORDER BY i.created_at DESC
                LIMIT 50
            """)
        )
    ).fetchall()

    total_row = await db.execute(
        text(f"""
            SELECT COUNT(*)
            FROM interactions i
            JOIN classifications pair_c
                ON pair_c.event_id = i.id AND pair_c.model_name = 'pair_classifier'
            JOIN classifications tax_c
                ON tax_c.event_id = i.id AND tax_c.model_name = 'taxonomy_classifier'
            WHERE {_DISAGREEMENT_WHERE}
        """)
    )
    total = total_row.scalar() or 0

    def _parse_labels(raw: object) -> list[str]:
        if isinstance(raw, list):
            return raw
        if isinstance(raw, str):
            return json.loads(raw)
        return []

    samples = [
        DisagreementSample(
            event_id=row[0],
            prompt_text=(row[1] or "")[:200],
            pair_label=row[2],
            taxonomy_labels=_parse_labels(row[3]),
        )
        for row in rows
    ]
    return DisagreementsResponse(total=total, samples=samples)


@router.get("/timeseries", response_model=TimeseriesResponse)
async def get_timeseries(
    db: AsyncSession = Depends(get_db),
    bucket_minutes: int = Query(default=60, ge=1, le=1440),
) -> TimeseriesResponse:
    """Per-model F1/precision/recall bucketed by time window."""
    result = await db.execute(
        select(
            ClassificationResult.model_name,
            ClassificationResult.predicted_label,
            ClassificationResult.processed_at,
            Interaction.ground_truth_safe,
        )
        .join(Interaction, ClassificationResult.event_id == Interaction.id)
        .where(Interaction.ground_truth_safe.is_not(None))
        .order_by(ClassificationResult.processed_at)
    )
    rows = result.all()

    # Group by (model_name, time bucket) in Python — cross-dialect compatible
    bucket_td = timedelta(minutes=bucket_minutes)

    def _bucket(ts: datetime) -> datetime:
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        epoch = datetime(1970, 1, 1, tzinfo=UTC)
        bucket_n = int((ts - epoch).total_seconds() // bucket_td.total_seconds())
        return epoch + bucket_n * bucket_td

    by_model: dict[str, dict[datetime, list[tuple[int, int]]]] = defaultdict(lambda: defaultdict(list))
    for model_name, predicted_label, processed_at, ground_truth_safe in rows:
        y_true = 0 if ground_truth_safe else 1
        by_model[model_name][_bucket(processed_at)].append((predicted_label, y_true))

    models: list[ModelTimeseries] = []
    for model_name, buckets in sorted(by_model.items()):
        points: list[MetricPoint] = []
        for bucket_ts in sorted(buckets):
            pairs = buckets[bucket_ts]
            f1, precision, recall = _compute_metrics(pairs)
            points.append(MetricPoint(
                bucket=bucket_ts,
                f1=f1,
                precision=precision,
                recall=recall,
                sample_count=len(pairs),
            ))
        models.append(ModelTimeseries(model_name=model_name, points=points))

    return TimeseriesResponse(models=models, bucket_minutes=bucket_minutes)


@router.get("/taxonomy/timeseries", response_model=TaxonomyTimeseriesResponse)
async def get_taxonomy_timeseries(
    db: AsyncSession = Depends(get_db),
    bucket_minutes: int = Query(default=60, ge=1, le=1440),
) -> TaxonomyTimeseriesResponse:
    """Taxonomy category flag counts bucketed by time window."""
    result = await db.execute(
        select(
            ClassificationResult.taxonomy_labels,
            ClassificationResult.processed_at,
        )
        .where(ClassificationResult.model_name == "taxonomy_classifier")
        .where(ClassificationResult.taxonomy_labels.is_not(None))
        .order_by(ClassificationResult.processed_at)
    )
    rows = result.all()

    bucket_td = timedelta(minutes=bucket_minutes)

    def _bucket(ts: datetime) -> datetime:
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        epoch = datetime(1970, 1, 1, tzinfo=UTC)
        bucket_n = int((ts - epoch).total_seconds() // bucket_td.total_seconds())
        return epoch + bucket_n * bucket_td

    def _parse_labels(raw: object) -> list[str]:
        if isinstance(raw, list):
            return raw
        if isinstance(raw, str):
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        return []

    by_bucket: dict[datetime, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    all_categories: set[str] = set()

    for taxonomy_labels, processed_at in rows:
        labels = _parse_labels(taxonomy_labels)
        if not labels:
            continue
        b = _bucket(processed_at)
        for label in labels:
            by_bucket[b][label] += 1
            all_categories.add(label)

    buckets: list[TaxonomyBucket] = [
        TaxonomyBucket(bucket=b, counts=dict(counts))
        for b, counts in sorted(by_bucket.items())
    ]

    return TaxonomyTimeseriesResponse(
        buckets=buckets,
        categories=sorted(all_categories),
        bucket_minutes=bucket_minutes,
    )


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
