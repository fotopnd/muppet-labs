from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from red_team_platform.models import Base


class BiasProbe(Base):
    __tablename__ = "bias_probes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id: Mapped[str] = mapped_column(String(20), nullable=False)
    government: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    probe_question_en: Mapped[str] = mapped_column(Text, nullable=False)
    divergence_hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    variants: Mapped[list[BiasPromptVariant]] = relationship(
        "BiasPromptVariant", back_populates="probe"
    )

    __table_args__ = (Index("uix_bias_probes_topic_id", "topic_id", unique=True),)


class BiasPromptVariant(Base):
    __tablename__ = "bias_prompt_variants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    probe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bias_probes.id"), nullable=False
    )
    language: Mapped[str] = mapped_column(String(5), nullable=False)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    probe: Mapped[BiasProbe] = relationship("BiasProbe", back_populates="variants")
    responses: Mapped[list[BiasResponse]] = relationship("BiasResponse", back_populates="variant")

    __table_args__ = (
        Index("uix_bias_prompt_variants_probe_language", "probe_id", "language", unique=True),
    )


class BiasResponse(Base):
    __tablename__ = "bias_responses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bias_prompt_variants.id"), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    variant: Mapped[BiasPromptVariant] = relationship(
        "BiasPromptVariant", back_populates="responses"
    )

    __table_args__ = (
        Index("uix_bias_responses_variant_model", "variant_id", "model_name", unique=True),
    )


class BiasDivergenceScore(Base):
    __tablename__ = "bias_divergence_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    probe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bias_probes.id"), nullable=False
    )
    language: Mapped[str] = mapped_column(String(5), nullable=False)
    en_response_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bias_responses.id"), nullable=False
    )
    other_response_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bias_responses.id"), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    cosine_distance: Mapped[float] = mapped_column(Float, nullable=False)
    back_translation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        Index(
            "uix_bias_div_scores_probe_lang_model",
            "probe_id",
            "language",
            "model_name",
            unique=True,
        ),
    )
