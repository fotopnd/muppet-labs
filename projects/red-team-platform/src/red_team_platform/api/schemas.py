from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


def compute_triage_tier(score: float) -> str:
    """Classify a classifier_score into a triage tier at query time (not stored)."""
    if score < 0.15:
        return "auto_safe"
    if score < 0.75:
        return "review"
    return "auto_flag"


# --- Attacks ---
class AttackOut(BaseModel):
    id: uuid.UUID
    source: str
    source_id: str
    harm_category: str
    strategy: str
    attack_text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AttackListOut(BaseModel):
    items: list[AttackOut]
    total: int
    page: int
    page_size: int


# --- Sessions ---
class SessionOut(BaseModel):
    id: uuid.UUID
    model_name: str
    total_attacks: int
    total_successes: int
    asr: float
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Runs ---
class RunOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    attack_id: uuid.UUID
    model_name: str
    response_text: str
    jailbreak_success: bool
    classifier_score: float
    latency_ms: int
    created_at: datetime
    harm_category: str
    strategy: str
    attack_text: str
    triage_tier: str

    model_config = {"from_attributes": True}


class RunListOut(BaseModel):
    items: list[RunOut]
    total: int
    page: int
    page_size: int


# --- Sample Review ---
class SampleOut(BaseModel):
    run_id: uuid.UUID
    attack_text: str
    response_text: str
    harm_category: str
    strategy: str
    jailbreak_success: bool
    classifier_score: float
    latency_ms: int
    model_name: str
    session_id: uuid.UUID
    created_at: datetime


# --- Coverage Heatmap ---
class CoverageCell(BaseModel):
    harm_category: str
    strategy: str
    total_runs: int
    total_successes: int
    asr: float


class CoverageOut(BaseModel):
    cells: list[CoverageCell]
    harm_categories: list[str]
    strategies: list[str]


# --- Strategy Comparison ---
class StrategyBar(BaseModel):
    strategy: str
    total_runs: int
    total_successes: int
    asr: float


class StrategyComparisonOut(BaseModel):
    bars: list[StrategyBar]


# --- Regression Tracker ---
class RegressionPoint(BaseModel):
    session_id: uuid.UUID
    model_name: str
    asr: float
    total_attacks: int
    created_at: datetime


class RegressionOut(BaseModel):
    points: list[RegressionPoint]
    model_names: list[str]


# --- Filter helpers ---
class FilterValuesOut(BaseModel):
    values: list[str]


# --- Clusters ---
class ClusterSummaryOut(BaseModel):
    cluster_id: int
    size: int
    top_harm_category: str
    top_strategy: str
    representative_text: str
    computed_at: datetime

    model_config = {"from_attributes": True}


class ClustersOut(BaseModel):
    summaries: list[ClusterSummaryOut]


class ClusterMemberOut(BaseModel):
    run_id: uuid.UUID
    cluster_id: int
    attack_text: str
    harm_category: str
    strategy: str
    classifier_score: float
    jailbreak_success: bool
    latency_ms: int
    model_name: str


class ClusterMembersOut(BaseModel):
    cluster_id: int
    members: list[ClusterMemberOut]


# --- Bias Heatmap ---
class BiasScoreRow(BaseModel):
    topic_id: str
    government: str
    label: str
    zh_score: float | None
    ru_score: float | None
    ar_score: float | None


class BiasScoresOut(BaseModel):
    rows: list[BiasScoreRow]
    scored_model: str | None


class BiasModelScoreRow(BaseModel):
    topic_id: str
    government: str
    label: str
    model_name: str
    zh_score: float | None
    ru_score: float | None
    ar_score: float | None


class BiasMultiModelOut(BaseModel):
    rows: list[BiasModelScoreRow]
    available_models: list[str]


# --- Model × Category Heatmap ---
class ModelCategoryCell(BaseModel):
    model_name: str
    harm_category: str
    total_runs: int
    total_successes: int
    asr: float


class ModelCategoryHeatmapOut(BaseModel):
    cells: list[ModelCategoryCell]
    models: list[str]
    categories: list[str]


# --- Attack Summary ---
class AttackSummaryOut(BaseModel):
    total: int
    top_category: str | None
    top_strategy: str | None


# --- Regression Category Delta ---
class CategoryDeltaItem(BaseModel):
    harm_category: str
    baseline_asr: float
    latest_asr: float
    delta: float


class CategoryDeltaOut(BaseModel):
    items: list[CategoryDeltaItem]
    baseline_session_id: uuid.UUID | None
    latest_session_id: uuid.UUID | None
    model_name: str | None


# --- Bias Response Viewer ---
class BiasLangDetail(BaseModel):
    prompt: str
    response: str | None
    cosine_distance: float | None
    back_translation: str | None


class BiasTopicResponseOut(BaseModel):
    topic_id: str
    government: str
    label: str
    languages: dict[str, BiasLangDetail]


# --- Top Failures ---
class TopFailureOut(BaseModel):
    run_id: uuid.UUID
    strategy: str
    harm_category: str
    model_name: str
    classifier_score: float
    attack_text: str
    response_text: str


class TopFailuresOut(BaseModel):
    items: list[TopFailureOut]


# --- Back Translation ---
class BackTranslateIn(BaseModel):
    text: str
    source_lang: Literal["zh", "ru", "ar"]


class BackTranslateOut(BaseModel):
    translated: str


# --- Case Review ---
class CaseReviewCreate(BaseModel):
    decision: Literal["approve", "flag", "escalate"]
    reason: str | None = None
    reviewer: str = "analyst-1"


class CaseReviewOut(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    decision: str
    reason: str | None
    reviewed_at: datetime
    reviewer: str

    model_config = {"from_attributes": True}


# --- Audit Log ---
class AuditLogEntryOut(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    action: str
    decision: str
    reason: str | None
    reviewer: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogOut(BaseModel):
    items: list[AuditLogEntryOut]
    total: int
    limit: int
    offset: int


# --- Triage Summary ---
class TriageSummaryOut(BaseModel):
    auto_safe: int
    review: int
    auto_flag: int
