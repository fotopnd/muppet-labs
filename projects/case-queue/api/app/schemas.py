from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import Action, ActorRole, CaseCategory, CaseStatus, Severity


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int


class DecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_id: str
    actor_role: ActorRole
    action: Action
    notes: str
    created_at: datetime


class CaseListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: CaseCategory
    severity: Severity
    status: CaseStatus
    created_at: datetime


class CaseDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content: str
    category: CaseCategory
    severity: Severity
    status: CaseStatus
    source: str
    meta: dict
    created_at: datetime
    updated_at: datetime
    decisions: list[DecisionRead]


class DecisionCreate(BaseModel):
    action: Action
    notes: str = Field(min_length=1)


class AuditEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    actor_id: str
    actor_role: ActorRole
    action: Action
    notes: str
    created_at: datetime
