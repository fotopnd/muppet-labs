from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class Action(StrEnum):
    approve = "approve"
    reject = "reject"
    escalate = "escalate"


class CaseListItem(BaseModel):
    id: str
    category: str
    severity: str
    status: str
    created_at: str


class CaseDetail(BaseModel):
    id: str
    content: str
    category: str
    severity: str
    status: str
    source: str


class Page(BaseModel):
    items: list[CaseListItem]
    total: int
    page: int
    page_size: int


class ClassificationResult(BaseModel):
    action: Action
    confidence: float  # 0.0 – 1.0
    reasoning: str
