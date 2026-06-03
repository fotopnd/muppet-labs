from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Double, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Classification(Base):
    __tablename__ = "classifications"
    __table_args__ = (
        Index("ix_classifications_group_model_created", "group", "model_name", "created_at"),
        Index("ix_classifications_event_group", "event_id", "group"),
        Index("ix_classifications_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(String, nullable=False)
    # "group" is a SQL reserved word — SQLAlchemy quotes it automatically in Postgres DDL
    group: Mapped[str] = mapped_column("group", String, nullable=False)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    predicted_label: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Double, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Double, nullable=False)
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AnomalyFlag(Base):
    __tablename__ = "anomaly_flags"
    __table_args__ = (Index("ix_anomaly_flags_window_start", "window_start"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    signal_name: Mapped[str] = mapped_column(String, nullable=False)
    z_score: Mapped[float] = mapped_column(Double, nullable=False)
    value: Mapped[float] = mapped_column(Double, nullable=False)
    baseline_mean: Mapped[float] = mapped_column(Double, nullable=False)
    baseline_std: Mapped[float] = mapped_column(Double, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Escalation(Base):
    __tablename__ = "escalations"
    __table_args__ = (Index("ix_escalations_created_at", "created_at"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    case_queue_case_id: Mapped[str] = mapped_column(String, nullable=False)
    escalation_reason: Mapped[str] = mapped_column(String, nullable=False)
    confidence_max: Mapped[float | None] = mapped_column(Double, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
