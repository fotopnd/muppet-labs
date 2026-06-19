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
    player_verdict: Literal["ACCEPT", "REJECT", "ESCALATE"]
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
    total_escalated: int = 0
    category_tiers: dict[str, int] = {}


# ── Responses ─────────────────────────────────────────────────────────────────


class SessionCreated(BaseModel):
    session_id: int
    share_id: str


class SessionResult(BaseModel):
    share_id: str
    total_days: int | None
    total_decisions: int | None
    accuracy: float | None
    game_over_condition: str | None
    phase_reached: int | None
    agreement_rate: float | None
    calibration_accuracy: float | None
    total_escalated: int | None


class BatchAccepted(BaseModel):
    accepted: int


class CardOut(BaseModel):
    id: int
    prompt_text: str
    response_text: str
    harm_category: str
    phase: int
    generation_tier: int
    is_harmful: bool
    gork_verdict: bool | None
    gork_confidence: float | None
    gork_reasoning: str | None
    agent_condition: Literal["none", "tier_1", "tier_2", "tier_3"]


class DealOut(BaseModel):
    phase_1: list[CardOut]
    phase_2: list[CardOut]
    phase_3: list[CardOut]


class AnalyticsSummary(BaseModel):
    total_sessions: int
    sessions_today: int
    avg_accuracy: float
    agreement_rate: float
    override_accuracy: float
    escalation_rate: float
    avg_latency_ms: float
    sessions_by_day: list[dict]
    accuracy_by_category: dict[str, float]


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
