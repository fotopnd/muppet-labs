from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from moderation_dashboard.api.database import get_db
from moderation_dashboard.api.schemas import (
    AnalyticsResponse,
    AnomalyFlagRead,
    CategoryTrend,
    DisagreementSample,
    DisagreementsResponse,
    DisagreementVerdict,
    EscalationRatePoint,
    EventComparison,
    ModelAccuracyPoint,
    ModelMetrics,
    ModelStatus,
    SingleModelVerdict,
    SparklinePoint,
    SparklineResponse,
    StreamMetrics,
    StreamTimeSeriesPoint,
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

_SEEDED_COUNTS_SQL = text("""
    SELECT model_name, COUNT(*) AS cnt
    FROM classifications
    WHERE seeded = true
    GROUP BY model_name
""")

# Live counts from the shadow group (all events, all models), excluding seeded rows
_LIVE_COUNTS_SQL = text("""
    SELECT
        model_name,
        COUNT(*) FILTER (WHERE seeded = false)                         AS live_event_count,
        COUNT(*) FILTER (WHERE seeded = false AND predicted_label = 1) AS live_flagged_count
    FROM classifications
    WHERE "group" = 'shadow'
    GROUP BY model_name
""")

# Disagreements: per-category breakdown in the last hour, one row per unique disagreement event
_DISAGREEMENTS_CATEGORY_SQL = text("""
    WITH disagreement_events AS (
        SELECT DISTINCT ON (e.event_id) e.event_id, c.category
        FROM escalations e
        JOIN classifications c ON c.event_id = e.event_id AND c."group" = 'shadow'
        WHERE e.escalation_reason = 'model_disagreement'
          AND e.created_at >= NOW() - INTERVAL '1 hour'
        ORDER BY e.event_id, c.created_at DESC
    )
    SELECT category, COUNT(*) AS cnt
    FROM disagreement_events
    GROUP BY category
""")

# Disagreement samples: up to 50 recent events, with shadow verdicts
_DISAGREEMENTS_SAMPLES_SQL = text("""
    WITH recent AS (
        SELECT event_id
        FROM escalations
        WHERE escalation_reason = 'model_disagreement'
        ORDER BY created_at DESC
        LIMIT 50
    )
    SELECT
        r.event_id,
        c.content,
        c.model_name,
        c.predicted_label,
        c.confidence
    FROM recent r
    JOIN classifications c ON c.event_id = r.event_id AND c."group" = 'shadow'
    ORDER BY r.event_id, c.model_name
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

# Sparkline: last N events for a model, bucketed into 5-minute windows over last hour
_SPARKLINE_SQL = text("""
    SELECT
        date_trunc('minute', created_at)
            - (EXTRACT(MINUTE FROM created_at)::int % 5) * INTERVAL '1 minute' AS window_start,
        SUM(CASE WHEN predicted_label = 1 AND correct     THEN 1 ELSE 0 END)::int AS tp,
        SUM(CASE WHEN predicted_label = 1 AND NOT correct THEN 1 ELSE 0 END)::int AS fp,
        SUM(CASE WHEN predicted_label = 0 AND NOT correct THEN 1 ELSE 0 END)::int AS fn
    FROM classifications
    WHERE model_name = :model_name
      AND "group" = 'production'
      AND created_at >= NOW() - INTERVAL '1 hour'
    GROUP BY 1
    ORDER BY 1 ASC
""")

# Stream time-series: event volume by category in 1-minute buckets, last 10 minutes
_TIMESERIES_SQL = text("""
    SELECT
        date_trunc('minute', created_at) AS bucket,
        category,
        COUNT(DISTINCT event_id) AS cnt
    FROM classifications
    WHERE created_at >= NOW() - INTERVAL '10 minutes'
    GROUP BY 1, 2
    ORDER BY 1 ASC
""")

# Analytics: category trends (hourly, last 48h)
_ANALYTICS_CATEGORY_SQL = text("""
    SELECT
        date_trunc('hour', created_at) AS event_hour,
        category,
        COUNT(DISTINCT event_id) AS event_count
    FROM classifications
    WHERE created_at >= NOW() - INTERVAL '48 hours'
    GROUP BY 1, 2
    ORDER BY 1 DESC
    LIMIT 500
""")

# Analytics: per-model hourly F1 (shadow group, last 24h)
_ANALYTICS_ACCURACY_SQL = text("""
    SELECT
        date_trunc('hour', created_at) AS classification_hour,
        "group",
        model_name,
        SUM(CASE WHEN predicted_label = 1 AND correct     THEN 1 ELSE 0 END)::int AS tp,
        SUM(CASE WHEN predicted_label = 1 AND NOT correct THEN 1 ELSE 0 END)::int AS fp,
        SUM(CASE WHEN predicted_label = 0 AND NOT correct THEN 1 ELSE 0 END)::int AS fn,
        COUNT(*) AS n
    FROM classifications
    WHERE created_at >= NOW() - INTERVAL '24 hours'
      AND "group" = 'shadow'
    GROUP BY 1, 2, 3
    ORDER BY 1 DESC
    LIMIT 500
""")

# Analytics: escalation rates in 5-minute windows (last 24h)
_ANALYTICS_ESCALATION_SQL = text("""
    WITH esc_by_window AS (
        SELECT
            date_trunc('minute', created_at)
                - (EXTRACT(MINUTE FROM created_at)::int % 5) * INTERVAL '1 minute' AS window_5min,
            COUNT(*) AS escalation_count
        FROM escalations
        WHERE escalation_reason != 'no_escalation'
          AND created_at >= NOW() - INTERVAL '24 hours'
        GROUP BY 1
    ),
    events_by_window AS (
        SELECT
            date_trunc('minute', created_at)
                - (EXTRACT(MINUTE FROM created_at)::int % 5) * INTERVAL '1 minute' AS window_5min,
            COUNT(DISTINCT event_id) AS total_events
        FROM classifications
        WHERE created_at >= NOW() - INTERVAL '24 hours'
          AND "group" = 'production'
        GROUP BY 1
    )
    SELECT
        ev.window_5min,
        COALESCE(esc.escalation_count, 0)                                              AS escalation_count,
        COALESCE(ev.total_events, 1)                                                   AS total_events,
        COALESCE(esc.escalation_count, 0)::float / GREATEST(COALESCE(ev.total_events, 1), 1) AS escalation_rate
    FROM events_by_window ev
    LEFT JOIN esc_by_window esc ON ev.window_5min = esc.window_5min
    ORDER BY ev.window_5min DESC
    LIMIT 200
""")


async def _get_seeded_counts(db: AsyncSession) -> dict[str, int]:
    result = await db.execute(_SEEDED_COUNTS_SQL)
    return {row.model_name: int(row.cnt) for row in result.fetchall()}


async def _get_live_counts(db: AsyncSession) -> dict[str, tuple[int, int]]:
    result = await db.execute(_LIVE_COUNTS_SQL)
    return {
        row.model_name: (int(row.live_event_count), int(row.live_flagged_count))
        for row in result.fetchall()
    }


def _build_model_metrics(
    rows: list[Any],
    seeded_counts: dict[str, int],
    group: str,
    live_counts: dict[str, tuple[int, int]] | None = None,
) -> list[ModelMetrics]:
    settings = get_settings()
    db_data: dict[str, Any] = {row.model_name: row for row in rows}
    live_set = set(settings.live_models)
    result: list[ModelMetrics] = []

    for model_key, spec in MODEL_REGISTRY.items():
        if spec.requires_checkpoint:
            checkpoint = getattr(settings, spec.checkpoint_path_env_var.lower(), None)
            status = ModelStatus.active if checkpoint else ModelStatus.pending_weights
        else:
            status = ModelStatus.active

        has_seeded = seeded_counts.get(model_key, 0) > 0
        source = "live" if model_key in live_set else "seeded"
        live_event_count, live_flagged_count = (live_counts or {}).get(model_key, (0, 0))

        if model_key in db_data:
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
                    source=source,
                    has_seeded_data=has_seeded,
                    live_event_count=live_event_count,
                    live_flagged_count=live_flagged_count,
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
                    source=source,
                    has_seeded_data=has_seeded,
                    live_event_count=live_event_count,
                    live_flagged_count=live_flagged_count,
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


@router.get("/metrics/stream/timeseries", response_model=list[StreamTimeSeriesPoint])
async def get_stream_timeseries(
    db: AsyncSession = Depends(get_db),
) -> list[StreamTimeSeriesPoint]:
    result = await db.execute(_TIMESERIES_SQL)
    rows = result.fetchall()

    # Pivot: bucket → {category: count}
    buckets: dict[Any, dict[str, int]] = {}
    for row in rows:
        bucket_key = row.bucket
        if bucket_key not in buckets:
            buckets[bucket_key] = {}
        buckets[bucket_key][row.category] = int(row.cnt)

    return [
        StreamTimeSeriesPoint(bucket=bucket, counts=counts)
        for bucket, counts in sorted(buckets.items())
    ]


@router.get("/metrics/sparkline", response_model=SparklineResponse)
async def get_sparkline(
    model_name: str = Query(..., description="Model key from MODEL_REGISTRY"),
    metric: str = Query("f1", description="Metric to plot (currently only f1 supported)"),
    db: AsyncSession = Depends(get_db),
) -> SparklineResponse:
    if model_name not in MODEL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown model: {model_name!r}")

    result = await db.execute(_SPARKLINE_SQL, {"model_name": model_name})
    rows = result.fetchall()

    points: list[SparklinePoint] = []
    for row in rows:
        tp, fp, fn = int(row.tp), int(row.fp), int(row.fn)
        denom = 2 * tp + fp + fn
        f1 = (2 * tp / denom) if denom > 0 else 0.0
        points.append(SparklinePoint(bucket=row.window_start, value=f1))

    return SparklineResponse(model_name=model_name, metric=metric, points=points)


@router.get("/metrics/production", response_model=list[ModelMetrics])
async def get_production_metrics(db: AsyncSession = Depends(get_db)) -> list[ModelMetrics]:
    rows_result = await db.execute(_METRICS_SQL, {"group_filter": "production"})
    seeded_counts = await _get_seeded_counts(db)
    live_counts = await _get_live_counts(db)
    return _build_model_metrics(rows_result.fetchall(), seeded_counts, "production", live_counts)


@router.get("/metrics/shadow", response_model=list[ModelMetrics])
async def get_shadow_metrics(db: AsyncSession = Depends(get_db)) -> list[ModelMetrics]:
    rows_result = await db.execute(_METRICS_SQL, {"group_filter": "shadow"})
    seeded_counts = await _get_seeded_counts(db)
    live_counts = await _get_live_counts(db)
    return _build_model_metrics(rows_result.fetchall(), seeded_counts, "shadow", live_counts)


@router.get("/metrics/all", response_model=list[ModelMetrics])
async def get_all_metrics(db: AsyncSession = Depends(get_db)) -> list[ModelMetrics]:
    """Merged view: each model's best available data (production group first, shadow as fallback)."""
    prod_result = await db.execute(_METRICS_SQL, {"group_filter": "production"})
    shadow_result = await db.execute(_METRICS_SQL, {"group_filter": "shadow"})
    seeded_counts = await _get_seeded_counts(db)
    live_counts = await _get_live_counts(db)

    prod_rows = {r.model_name: r for r in prod_result.fetchall()}
    shadow_rows = {r.model_name: r for r in shadow_result.fetchall()}
    # Merge: prefer shadow when it has active throughput (live model); else use production
    merged = {**prod_rows}
    for name, row in shadow_rows.items():
        prod = merged.get(name)
        shadow_active = float(row.throughput_per_sec or 0) > 0
        prod_active = float(prod.throughput_per_sec if prod else 0 or 0) > 0
        if shadow_active or (not prod_active and name not in merged):
            merged[name] = row

    return _build_model_metrics(list(merged.values()), seeded_counts, "production", live_counts)


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


@router.get("/metrics/disagreements", response_model=DisagreementsResponse)
async def get_disagreements(db: AsyncSession = Depends(get_db)) -> DisagreementsResponse:
    cat_result = await db.execute(_DISAGREEMENTS_CATEGORY_SQL)
    by_category = {row.category: int(row.cnt) for row in cat_result.fetchall()}
    total_last_hour = sum(by_category.values())

    sample_result = await db.execute(_DISAGREEMENTS_SAMPLES_SQL)
    rows = sample_result.fetchall()

    # Group rows by event_id, preserving insertion order; take first 10 unique events
    events: dict[str, list[Any]] = {}
    for row in rows:
        events.setdefault(row.event_id, []).append(row)

    samples: list[DisagreementSample] = []
    for event_id, event_rows in list(events.items())[:10]:
        content = event_rows[0].content[:140]
        verdicts = [
            DisagreementVerdict(
                model_name=r.model_name,
                predicted_label=int(r.predicted_label),
                confidence=float(r.confidence),
            )
            for r in event_rows
        ]
        samples.append(DisagreementSample(event_id=event_id, content=content, verdicts=verdicts))

    return DisagreementsResponse(
        total_last_hour=total_last_hour,
        by_category=by_category,
        samples=samples,
    )


@router.get("/metrics/analytics", response_model=AnalyticsResponse)
async def get_analytics(db: AsyncSession = Depends(get_db)) -> AnalyticsResponse:
    # Category trends: computed directly from classifications table
    cat_result = await db.execute(_ANALYTICS_CATEGORY_SQL)
    category_trends = [
        CategoryTrend(
            hour=row.event_hour,
            category=row.category,
            event_count=int(row.event_count),
        )
        for row in cat_result.fetchall()
    ]

    # Model accuracy: compute F1 per hour per model from raw TP/FP/FN
    acc_result = await db.execute(_ANALYTICS_ACCURACY_SQL)
    model_accuracy: list[ModelAccuracyPoint] = []
    for row in acc_result.fetchall():
        tp, fp, fn = int(row.tp), int(row.fp), int(row.fn)
        denom = 2 * tp + fp + fn
        f1 = (2 * tp / denom) if denom > 0 else 0.0
        model_accuracy.append(
            ModelAccuracyPoint(
                hour=row.classification_hour,
                group=row.group,
                model_name=row.model_name,
                f1=f1,
                n=int(row.n),
            )
        )

    # Escalation rates: 5-minute windows from escalations table
    esc_result = await db.execute(_ANALYTICS_ESCALATION_SQL)
    escalation_rates = [
        EscalationRatePoint(
            window_start=row.window_5min,
            escalation_count=int(row.escalation_count),
            total_events=int(row.total_events),
            escalation_rate=float(row.escalation_rate),
        )
        for row in esc_result.fetchall()
    ]

    return AnalyticsResponse(
        category_trends=category_trends,
        model_accuracy=model_accuracy,
        escalation_rates=escalation_rates,
    )
