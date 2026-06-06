from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class VerdictEntry(BaseModel):
    model_name: str
    predicted_label: int
    confidence: float
    taxonomy_labels: list[str] | None = None


class RecentEvent(BaseModel):
    event_id: UUID
    prompt_text: str
    response_text: str | None
    source_dataset: str
    verdicts: list[VerdictEntry]
    escalation_reason: str | None


class StreamResponse(BaseModel):
    events: list[RecentEvent]


class ModelMetrics(BaseModel):
    model_name: str
    f1: float
    precision: float
    recall: float
    sample_count: int


class MetricsResponse(BaseModel):
    models: list[ModelMetrics]


class CalibrationBin(BaseModel):
    bin_lower: float
    bin_upper: float
    count: int
    actual_positive_rate: float


class ModelCalibration(BaseModel):
    model_name: str
    bins: list[CalibrationBin]


class CalibrationResponse(BaseModel):
    models: list[ModelCalibration]


class DisagreementSample(BaseModel):
    event_id: UUID
    prompt_text: str
    pair_label: int | None
    taxonomy_labels: list[str] | None
    escalation_reason: str | None = None


class DisagreementsResponse(BaseModel):
    total: int
    samples: list[DisagreementSample]
