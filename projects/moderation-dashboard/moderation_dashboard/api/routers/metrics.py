from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from moderation_dashboard.api.database import get_db
from moderation_dashboard.api.schemas import (
    AnalyticsResponse,
    AnomalyFlagRead,
    CategoryTrend,
    EscalationRatePoint,
    EventComparison,
    ModelAccuracyPoint,
    ModelMetrics,
    ModelStatus,
    SingleModelVerdict,
    StreamMetrics,
)
from moderation_dashboard.config import MODEL_REGISTRY, get_settings

router = APIRouter(tags=["metrics"])
logger = logging.getLogger(__name__)

# SQL: per-group metrics — call with :group_filter = 'production' or 'shadow'
_METRICS_SQL = text("""
    SELECT
        model_name,
        COUNT(DISTINCT event_id)                                                     AS event_count,
        SUM(CASE WHEN predicted_label = 1 AND correct     THEN 1 ELSE 0 END)        AS tp,
        SUM(CASE WHEN predicted_label = 1 AND NOT correct THEN 1 ELSE 0 END)        AS fp,
        SUM(CASE WHEN predicted_label = 0 AND NOT correct THEN 1 ELSE 0 END)        AS fn,
        COALESCE(percentile_cont(0.5)  WITHIN GROUP (ORDER BY latency_ms), 0)       AS latency_p50,
        COALESCE(percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms), 0)       AS latency_p95,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '60 seconds') / 60.0  AS throughput_per_sec
    FROM classifications
    WHERE "group" = :group_filter
    GROUP BY model_name
""")

_STREAM_RATE_SQL = text("""
    SELECT COUNT(DISTINCT event_id)
    FROM classifications
    WHERE created_at >= NOW() - INTERVAL '60 seconds'
""")

_STREAM_CATEGORY_SQL = text("""
    SELECT category, COUNT(DISTINCT event_id) AS cnt
    FROM classifications
    WHERE created_at >= NOW() - INTERVAL '5 minutes'
    GROUP BY category
""")

_STREAM_TOTAL_SQL = text("""
    SELECT COUNT(DISTINCT event_id) FROM classifications
""")

_ANOMALIES_SQL = text("""
    SELECT id, window_start, window_end, signal_name, z_score, value,
           baseline_mean, baseline_std, created_at
    FROM anomaly_flags
    ORDER BY window_start DESC
    LIMIT 50
""")

_COMPARISON_SQL = text("""
    SELECT model_name, predicted_label, confidence, latency_ms, correct
    FROM classifications
    WHERE event_id = :event_id AND "group" = 'shadow'
""")


def _build_model_metrics(rows: list[Any], group: str) -> list[ModelMetrics]:
    settings = get_settings()
    db_data: dict[str, Any] = {row.model_name: row for row in rows}
    result: list[ModelMetrics] = []

    for model_key, spec in MODEL_REGISTRY.items():
        if spec.requires_checkpoint:
            checkpoint = getattr(settings, spec.checkpoint_path_env_var.lower(), None)
            status = ModelStatus.active if checkpoint else ModelStatus.pending_weights
        else:
            status = ModelStatus.active

        if model_key in db_data and status == ModelStatus.active:
            row = db_data[model_key]
            tp, fp, fn = int(row.tp), int(row.fp), int(row.fn)
            denom_f1 = 2 * tp + fp + fn
            denom_prec = tp + fp
            denom_rec = tp + fn
            f1 = (2 * tp / denom_f1) if denom_f1 > 0 else None
            precision = (tp / denom_prec) if denom_prec > 0 else None
            recall = (tp / denom_rec) if denom_rec > 0 else None
            result.append(
                ModelMetrics(
                    model_name=model_key,
                    display_name=spec.display_name,
                    status=status,
                    event_count=int(row.event_count),
                    f1=f1,
                    precision=precision,
                    recall=recall,
                    latency_p50=float(row.latency_p50),
                    latency_p95=float(row.latency_p95),
                    throughput_per_sec=float(row.throughput_per_sec),
                )
            )
        else:
            result.append(
                ModelMetrics(
                    model_name=model_key,
                    display_name=spec.display_name,
                    status=status,
                    event_count=0,
                    f1=None,
                    precision=None,
                    recall=None,
                    latency_p50=None,
                    latency_p95=None,
                    throughput_per_sec=None,
                )
            )

    return result


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/metrics/stream", response_model=StreamMetrics)
async def get_stream_metrics(db: AsyncSession = Depends(get_db)) -> StreamMetrics:
    rate_result = await db.execute(_STREAM_RATE_SQL)
    unique_recent = rate_result.scalar() or 0

    cat_result = await db.execute(_STREAM_CATEGORY_SQL)
    category_counts = {row.category: int(row.cnt) for row in cat_result.fetchall()}

    total_result = await db.execute(_STREAM_TOTAL_SQL)
    total = total_result.scalar() or 0

    return StreamMetrics(
        event_rate_per_sec=unique_recent / 60.0,
        category_counts=category_counts,
        total_events=int(total),
    )


@router.get("/metrics/production", response_model=list[ModelMetrics])
async def get_production_metrics(db: AsyncSession = Depends(get_db)) -> list[ModelMetrics]:
    result = await db.execute(_METRICS_SQL, {"group_filter": "production"})
    rows = result.fetchall()
    return _build_model_metrics(rows, "production")


@router.get("/metrics/shadow", response_model=list[ModelMetrics])
async def get_shadow_metrics(db: AsyncSession = Depends(get_db)) -> list[ModelMetrics]:
    result = await db.execute(_METRICS_SQL, {"group_filter": "shadow"})
    rows = result.fetchall()
    return _build_model_metrics(rows, "shadow")


@router.get("/metrics/comparison/{event_id}", response_model=EventComparison)
async def get_comparison(event_id: str, db: AsyncSession = Depends(get_db)) -> EventComparison:
    meta_result = await db.execute(
        text("""
            SELECT content, category
            FROM classifications
            WHERE event_id = :event_id
            LIMIT 1
        """),
        {"event_id": event_id},
    )
    meta = meta_result.fetchone()
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Event {event_id!r} not found")

    # Derive ground_truth: if predicted_label=1 and correct=True → GT=1; if pred=1 correct=False → GT=0
    gt_result = await db.execute(
        text("""
            SELECT predicted_label, correct
            FROM classifications
            WHERE event_id = :event_id
            LIMIT 1
        """),
        {"event_id": event_id},
    )
    gt_row = gt_result.fetchone()
    if gt_row is not None:
        if gt_row.correct:
            ground_truth = gt_row.predicted_label
        else:
            ground_truth = 1 - gt_row.predicted_label
    else:
        ground_truth = 0

    shadow_result = await db.execute(_COMPARISON_SQL, {"event_id": event_id})
    verdicts = [
        SingleModelVerdict(
            model_name=row.model_name,
            predicted_label=row.predicted_label,
            confidence=float(row.confidence),
            latency_ms=float(row.latency_ms),
            correct=bool(row.correct),
        )
        for row in shadow_result.fetchall()
    ]

    return EventComparison(
        event_id=event_id,
        content=meta.content,
        category=meta.category,
        ground_truth=ground_truth,
        classifications=verdicts,
    )


@router.get("/metrics/anomalies", response_model=list[AnomalyFlagRead])
async def get_anomalies(db: AsyncSession = Depends(get_db)) -> list[AnomalyFlagRead]:
    result = await db.execute(_ANOMALIES_SQL)
    rows = result.fetchall()
    return [
        AnomalyFlagRead(
            id=row.id,
            window_start=row.window_start,
            window_end=row.window_end,
            signal_name=row.signal_name,
            z_score=float(row.z_score),
            value=float(row.value),
            baseline_mean=float(row.baseline_mean),
            baseline_std=float(row.baseline_std),
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/metrics/analytics", response_model=AnalyticsResponse)
async def get_analytics(db: AsyncSession = Depends(get_db)) -> AnalyticsResponse:
    category_trends: list[CategoryTrend] = []
    model_accuracy: list[ModelAccuracyPoint] = []
    escalation_rates: list[EscalationRatePoint] = []

    try:
        cat_result = await db.execute(
            text("""
            SELECT event_hour, category, event_count
            FROM dbt_moderation.fct_category_trends
            ORDER BY event_hour DESC
            LIMIT 500
        """)
        )
        category_trends = [
            CategoryTrend(
                hour=row.event_hour, category=row.category, event_count=int(row.event_count)
            )
            for row in cat_result.fetchall()
        ]

        acc_result = await db.execute(
            text("""
            SELECT classification_hour, "group", model_name, f1, n
            FROM dbt_moderation.fct_model_accuracy
            ORDER BY classification_hour DESC
            LIMIT 500
        """)
        )
        model_accuracy = [
            ModelAccuracyPoint(
                hour=row.classification_hour,
                group=row.group,
                model_name=row.model_name,
                f1=float(row.f1),
                n=int(row.n),
            )
            for row in acc_result.fetchall()
        ]

        esc_result = await db.execute(
            text("""
            SELECT window_5min, escalation_count, total_events, escalation_rate
            FROM dbt_moderation.fct_escalation_rates
            ORDER BY window_5min DESC
            LIMIT 200
        """)
        )
        escalation_rates = [
            EscalationRatePoint(
                window_start=row.window_5min,
                escalation_count=int(row.escalation_count),
                total_events=int(row.total_events),
                escalation_rate=float(row.escalation_rate),
            )
            for row in esc_result.fetchall()
        ]
    except Exception:
        # dbt tables don't exist yet (dbt-refresh not yet run) — return empty lists
        logger.info("dbt mart tables not available; returning empty analytics", exc_info=True)

    return AnalyticsResponse(
        category_trends=category_trends,
        model_accuracy=model_accuracy,
        escalation_rates=escalation_rates,
    )
