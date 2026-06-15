from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Attack(Base):
    __tablename__ = "attacks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str] = mapped_column(String(200), nullable=False)
    harm_category: Mapped[str] = mapped_column(String(100), nullable=False)
    strategy: Mapped[str] = mapped_column(String(100), nullable=False)
    attack_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    runs: Mapped[list[Run]] = relationship("Run", back_populates="attack")

    __table_args__ = (
        Index("uix_attacks_source_source_id", "source", "source_id", unique=True),
        Index("ix_attacks_harm_category", "harm_category"),
        Index("ix_attacks_strategy", "strategy"),
    )


class RunSession(Base):
    __tablename__ = "run_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    total_attacks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_successes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    asr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    runs: Mapped[list[Run]] = relationship("Run", back_populates="session")

    __table_args__ = (
        Index("ix_run_sessions_model_name", "model_name"),
        Index("ix_run_sessions_created_at", "created_at"),
    )


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("run_sessions.id"), nullable=False
    )
    attack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attacks.id"), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    jailbreak_success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    classifier_score: Mapped[float] = mapped_column(Float, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    session: Mapped[RunSession] = relationship("RunSession", back_populates="runs")
    attack: Mapped[Attack] = relationship("Attack", back_populates="runs")

    __table_args__ = (
        Index("ix_runs_session_id", "session_id"),
        Index("ix_runs_attack_id", "attack_id"),
        Index("ix_runs_jailbreak_success", "jailbreak_success"),
    )


class FailureCluster(Base):
    __tablename__ = "failure_clusters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id: Mapped[int] = mapped_column(Integer, nullable=False)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        Index("ix_failure_clusters_cluster_id", "cluster_id"),
        Index("ix_failure_clusters_run_id", "run_id"),
    )


class ClusterSummary(Base):
    __tablename__ = "cluster_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id: Mapped[int] = mapped_column(Integer, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    top_harm_category: Mapped[str] = mapped_column(String(100), nullable=False)
    top_strategy: Mapped[str] = mapped_column(String(100), nullable=False)
    representative_text: Mapped[str] = mapped_column(Text, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    __table_args__ = (Index("uix_cluster_summaries_cluster_id", "cluster_id", unique=True),)


class CaseReview(Base):
    __tablename__ = "case_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    reviewer: Mapped[str] = mapped_column(String(100), nullable=False)

    __table_args__ = (Index("uix_case_reviews_run_id", "run_id", unique=True),)


class AuditLogEntry(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        Index("ix_audit_log_run_id", "run_id"),
        Index("ix_audit_log_created_at", "created_at"),
    )
