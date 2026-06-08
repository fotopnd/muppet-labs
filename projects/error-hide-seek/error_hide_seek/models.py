from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ErrorCategory(StrEnum):
    INVERTED_CONCLUSION = "inverted_conclusion"
    NUMBER_SUBSTITUTION = "number_substitution"
    FALSE_CITATION = "false_citation"
    SCOPE_EXTENSION = "scope_extension"
    CAUSAL_INVERSION = "causal_inversion"


# Ordered tuple used for round-robin category assignment. Import this rather
# than redefining locally so experiments and plant-errors always agree.
CATEGORY_CYCLE: tuple[str, ...] = tuple(c.value for c in ErrorCategory)


class Condition(StrEnum):
    UNAIDED = "unaided"
    AGENT_ONLY = "agent_only"
    HUMAN_AGENT = "human_agent"


class SessionStatus(StrEnum):
    OPEN = "open"
    COMPLETED = "completed"


class AgentRunStatus(StrEnum):
    SUCCESS = "success"
    PARSE_FAILED = "parse_failed"
    SKIPPED = "skipped"


class Paper(Base):
    __tablename__ = "papers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    arxiv_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str] = mapped_column(Text, nullable=False)
    categories: Mapped[str] = mapped_column(String(200), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class Experiment(Base):
    __tablename__ = "experiments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class ExperimentPaper(Base):
    __tablename__ = "experiment_papers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("experiments.id"), nullable=False, index=True
    )
    paper_id: Mapped[int] = mapped_column(Integer, ForeignKey("papers.id"), nullable=False)
    condition: Mapped[str] = mapped_column(String(20), nullable=False)
    intended_category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    __table_args__ = (UniqueConstraint("experiment_id", "paper_id"),)


class PlantedError(Base):
    __tablename__ = "planted_errors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(Integer, ForeignKey("papers.id"), nullable=False)
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("experiments.id"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    altered_text: Mapped[str] = mapped_column(Text, nullable=False)
    altered_abstract: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    __table_args__ = (UniqueConstraint("paper_id", "experiment_id"),)


class ReviewSession(Base):
    __tablename__ = "review_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("experiments.id"), nullable=False, index=True
    )
    paper_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("papers.id"), nullable=False, index=True
    )
    condition: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=SessionStatus.OPEN)
    agent_run_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    parse_failures: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AgentAnnotation(Base):
    __tablename__ = "agent_annotations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("review_sessions.id"), nullable=False, index=True
    )
    text_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(String(10), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class HumanDetection(Base):
    __tablename__ = "human_detections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("review_sessions.id"), nullable=False, index=True
    )
    text_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_true_positive: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
