from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CaseCategory(str, enum.Enum):
    toxic = "toxic"
    severe_toxic = "severe_toxic"
    obscene = "obscene"
    threat = "threat"
    insult = "insult"
    identity_hate = "identity_hate"


class Severity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class CaseStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    escalated = "escalated"


class Action(str, enum.Enum):
    approve = "approve"
    reject = "reject"
    escalate = "escalate"


class ActorRole(str, enum.Enum):
    reviewer = "reviewer"
    senior_reviewer = "senior_reviewer"


ACTION_TO_STATUS: dict[Action, CaseStatus] = {
    Action.approve: CaseStatus.approved,
    Action.reject: CaseStatus.rejected,
    Action.escalate: CaseStatus.escalated,
}


class Case(Base):
    __tablename__ = "cases"
    __table_args__ = (
        Index("ix_cases_status", "status"),
        Index("ix_cases_category", "category"),
        Index("ix_cases_severity", "severity"),
        Index("ix_cases_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[CaseCategory] = mapped_column(SAEnum(CaseCategory), nullable=False)
    severity: Mapped[Severity] = mapped_column(SAEnum(Severity), nullable=False)
    status: Mapped[CaseStatus] = mapped_column(
        SAEnum(CaseStatus), nullable=False, default=CaseStatus.pending
    )
    source: Mapped[str] = mapped_column(String, nullable=False)
    meta: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    decisions: Mapped[list[Decision]] = relationship(
        "Decision", back_populates="case", order_by="Decision.created_at"
    )


class Decision(Base):
    __tablename__ = "decisions"
    __table_args__ = (
        Index("ix_decisions_case_id", "case_id"),
        Index("ix_decisions_actor_id", "actor_id"),
        Index("ix_decisions_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(String, ForeignKey("cases.id"), nullable=False)
    actor_id: Mapped[str] = mapped_column(String, nullable=False)
    actor_role: Mapped[ActorRole] = mapped_column(SAEnum(ActorRole), nullable=False)
    action: Mapped[Action] = mapped_column(SAEnum(Action), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    case: Mapped[Case] = relationship("Case", back_populates="decisions")
