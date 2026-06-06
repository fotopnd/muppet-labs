from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_dataset: Mapped[str] = mapped_column(String(50), nullable=False)
    ground_truth_safe: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ground_truth_categories: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    escalated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    escalation_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)

    classifications: Mapped[list[ClassificationResult]] = relationship(
        back_populates="interaction", lazy="select"
    )


class ClassificationResult(Base):
    __tablename__ = "classifications"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    predicted_label: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    seeded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # New columns for llm-safety-monitor
    event_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("interactions.id"), nullable=True, index=True
    )
    taxonomy_labels: Mapped[list | None] = mapped_column(JSON, nullable=True)

    interaction: Mapped[Interaction | None] = relationship(
        back_populates="classifications"
    )
