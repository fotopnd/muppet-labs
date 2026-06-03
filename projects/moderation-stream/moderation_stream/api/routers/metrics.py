from __future__ import annotations

from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from moderation_stream.api.database import get_db
from moderation_stream.api.schemas import MetricsResponse, ModelMetrics, ModelStatus
from moderation_stream.config import MODEL_REGISTRY, Settings

router = APIRouter(tags=["metrics"])

METRICS_SQL = text("""
    SELECT
        model_name,
        COUNT(*)                                                                     AS total_processed,
        SUM(correct::int)                                                            AS correct,
        AVG(correct::int::float)                                                     AS accuracy,
        COALESCE(percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms), 0)         AS p50_latency_ms,
        COALESCE(percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms), 0)        AS p95_latency_ms,
        COALESCE(
            COUNT(*) FILTER (WHERE processed_at >= NOW() - INTERVAL '60 seconds') / 60.0,
            0
        )                                                                            AS throughput_cps
    FROM classification_results
    GROUP BY model_name
""")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def _build_response(rows: list[Any], settings: Settings) -> MetricsResponse:
    db_data: dict[str, Any] = {row.model_name: row for row in rows}
    models = []

    for entry in MODEL_REGISTRY:
        name: str = entry["model_name"]
        phase: int = entry["phase"]

        if phase == 1:
            status = ModelStatus.ACTIVE
        else:
            checkpoint = getattr(settings, entry["checkpoint_field"], None)
            status = ModelStatus.ACTIVE if checkpoint else ModelStatus.PENDING_WEIGHTS

        if name in db_data and status == ModelStatus.ACTIVE:
            row = db_data[name]
            models.append(ModelMetrics(
                model_name=name,
                status=status,
                total_processed=int(row.total_processed),
                correct=int(row.correct) if row.correct is not None else None,
                accuracy=float(row.accuracy) if row.accuracy is not None else None,
                p50_latency_ms=float(row.p50_latency_ms),
                p95_latency_ms=float(row.p95_latency_ms),
                throughput_cps=float(row.throughput_cps),
            ))
        else:
            models.append(ModelMetrics(
                model_name=name,
                status=status,
                total_processed=0,
                correct=None,
                accuracy=None,
                p50_latency_ms=0.0,
                p95_latency_ms=0.0,
                throughput_cps=0.0,
            ))

    return MetricsResponse(models=models, generated_at=datetime.now(UTC))


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MetricsResponse:
    result = await db.execute(METRICS_SQL)
    rows = result.fetchall()
    return _build_response(rows, settings)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
