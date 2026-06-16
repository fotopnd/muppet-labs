from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

# ── Requests ──────────────────────────────────────────────────────────────────


class CreateSessionRequest(BaseModel):
    started_at: datetime


class DecisionItem(BaseModel):
    document_id: int
    agent_condition: Literal["none", "tier_1", "tier_2", "tier_3"]
    player_verdict: Literal["CLEAR", "REDACT", "ESCALATE"]
    player_correct: bool
    latency_ms: float
    agreed_with_agent: bool | None
    bars: dict[str, int]
    game_day: int
    phase: int
    category_tier: int
    is_calibration: bool


class BatchDecisionsRequest(BaseModel):
    session_id: int
    game_day: int
    decisions: list[DecisionItem]


class PatchSessionRequest(BaseModel):
    ended_at: datetime
    total_days: int
    total_decisions: int
    correct_decisions: int
    accuracy: float
    phase_reached: int
    game_over_condition: str
    final_bars: dict[str, int]
    compliance_profile: dict[str, int | float]
    calibration_accuracy: float
    calibration_decisions: int
    category_tiers: dict[str, int]


# ── Responses ─────────────────────────────────────────────────────────────────


class SessionCreated(BaseModel):
    session_id: int


class BatchAccepted(BaseModel):
    accepted: int


class CardOut(BaseModel):
    id: int
    document_text: str
    harm_category: str
    phase: int
    generation_tier: int
    is_harmful: bool
    gork_verdict: bool | None
    gork_confidence: float | None
    gork_reasoning: str | None
    agent_condition: Literal["none", "tier_1", "tier_2", "tier_3"]


class AnalyticsSummary(BaseModel):
    total_sessions: int
    sessions_today: int
    global_fp_rate: float
    global_fn_rate: float
    avg_latency_ms: float
    phase_survival: dict[str, float]
    system_drift_error_rate: list[dict]
    escalation_rate: float
    escalation_rate_by_category: dict[str, float]


class UpliftRow(BaseModel):
    document_id: int
    strategy: str
    harm_category: str
    generation_model: str
    is_harmful: bool
    no_agent_decisions: int
    no_agent_accuracy: float
    agent_decisions: int
    agent_accuracy: float
    document_uplift: float
