from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class ModelStatus(StrEnum):
    ACTIVE = "active"
    PENDING_WEIGHTS = "pending_weights"


class ModelMetrics(BaseModel):
    model_name: str
    status: ModelStatus
    total_processed: int
    correct: int | None
    accuracy: float | None
    p50_latency_ms: float
    p95_latency_ms: float
    throughput_cps: float


class MetricsResponse(BaseModel):
    models: list[ModelMetrics]
    generated_at: datetime
