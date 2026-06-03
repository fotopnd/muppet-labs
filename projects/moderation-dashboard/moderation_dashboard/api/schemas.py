from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class ModelStatus(StrEnum):
    active = "active"
    pending_weights = "pending_weights"


class ModelMetrics(BaseModel):
    model_name: str
    display_name: str
    status: ModelStatus
    event_count: int
    f1: float | None
    precision: float | None
    recall: float | None
    latency_p50: float | None
    latency_p95: float | None
    throughput_per_sec: float | None


class SingleModelVerdict(BaseModel):
    model_name: str
    predicted_label: int
    confidence: float
    latency_ms: float
    correct: bool


class EventComparison(BaseModel):
    event_id: str
    content: str
    category: str
    ground_truth: int
    classifications: list[SingleModelVerdict]


class AnomalyFlagRead(BaseModel):
    id: str
    window_start: datetime
    window_end: datetime
    signal_name: str
    z_score: float
    value: float
    baseline_mean: float
    baseline_std: float
    created_at: datetime


class StreamMetrics(BaseModel):
    event_rate_per_sec: float
    category_counts: dict[str, int]
    total_events: int


class CategoryTrend(BaseModel):
    hour: datetime
    category: str
    event_count: int


class ModelAccuracyPoint(BaseModel):
    hour: datetime
    group: str
    model_name: str
    f1: float
    n: int


class EscalationRatePoint(BaseModel):
    window_start: datetime
    escalation_count: int
    total_events: int
    escalation_rate: float


class AnalyticsResponse(BaseModel):
    category_trends: list[CategoryTrend]
    model_accuracy: list[ModelAccuracyPoint]
    escalation_rates: list[EscalationRatePoint]
