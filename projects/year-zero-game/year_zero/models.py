from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DocumentLibrary(Base):
    __tablename__ = "document_library"
    __table_args__ = (
        CheckConstraint("generation_tier BETWEEN 1 AND 3", name="ck_generation_tier"),
        CheckConstraint("phase BETWEEN 1 AND 3", name="ck_phase"),
        Index("ix_document_library_strategy", "strategy"),
        Index("ix_document_library_harm_category", "harm_category"),
        Index("ix_document_library_generation_model", "generation_model"),
        Index("ix_document_library_phase", "phase"),
        Index("ix_document_library_is_harmful", "is_harmful"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt_text: Mapped[str] = mapped_column(Text)
    document_text: Mapped[str] = mapped_column(Text)
    generation_model: Mapped[str] = mapped_column(String(50))
    generation_tier: Mapped[int] = mapped_column(Integer)
    strategy: Mapped[str] = mapped_column(String(50))
    harm_category: Mapped[str] = mapped_column(String(50))
    is_harmful: Mapped[bool] = mapped_column(Boolean)
    phase: Mapped[int] = mapped_column(Integer)
    sovereign_verdict: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    sovereign_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    sovereign_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    verdict_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    target_condition_mix: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    served_none: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    served_tier_1: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    served_tier_2: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    served_tier_3: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class GameSession(Base):
    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_decisions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correct_decisions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    phase_reached: Mapped[int | None] = mapped_column(Integer, nullable=True)
    game_over_condition: Mapped[str | None] = mapped_column(String(30), nullable=True)
    final_bar_public_trust: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_bar_security: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_bar_treasury: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_bar_legitimacy: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_bar_compliance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_agreements: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_overrides: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_no_agent_decisions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    agreement_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    correct_agreements: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correct_overrides: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correct_no_agent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calibration_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    calibration_decisions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category_tiers: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class PlayerDecision(Base):
    __tablename__ = "player_decisions"
    __table_args__ = (
        CheckConstraint(
            "player_verdict IN ('CLEAR', 'REDACT', 'ESCALATE')", name="ck_player_verdict"
        ),
        Index("ix_player_decisions_session_id", "session_id"),
        Index("ix_player_decisions_document_id", "document_id"),
        Index("ix_player_decisions_agent_condition", "agent_condition"),
        Index("ix_player_decisions_player_correct", "player_correct"),
        Index("ix_player_decisions_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("game_sessions.id"))
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("document_library.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    agent_condition: Mapped[str] = mapped_column(String(10))
    player_verdict: Mapped[str] = mapped_column(String(10))
    player_correct: Mapped[bool] = mapped_column(Boolean)
    latency_ms: Mapped[float] = mapped_column(Float)
    agreed_with_agent: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    bar_public_trust: Mapped[int] = mapped_column(Integer)
    bar_security: Mapped[int] = mapped_column(Integer)
    bar_treasury: Mapped[int] = mapped_column(Integer)
    bar_legitimacy: Mapped[int] = mapped_column(Integer)
    bar_compliance: Mapped[int] = mapped_column(Integer)
    game_day: Mapped[int] = mapped_column(Integer)
    phase: Mapped[int] = mapped_column(Integer)
    category_tier: Mapped[int] = mapped_column(Integer)
    is_calibration: Mapped[bool] = mapped_column(Boolean, default=False)
