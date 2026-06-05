from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from moderation_dashboard.api.database import get_db
from moderation_dashboard.api.models import CaseDecision
from moderation_dashboard.api.schemas import (
    CaseDecisionCreate,
    CaseDecisionRead,
    EscalationCaseRead,
)

router = APIRouter(tags=["cases"])
logger = logging.getLogger(__name__)

_CASES_SQL = text("""
    SELECT
        e.id,
        e.event_id,
        e.escalation_reason,
        e.confidence_max,
        e.created_at,
        c.content,
        c.category,
        cd.action,
        cd.notes
    FROM escalations e
    JOIN LATERAL (
        SELECT content, category
        FROM classifications
        WHERE event_id = e.event_id
        LIMIT 1
    ) c ON true
    LEFT JOIN case_decisions cd ON cd.escalation_id = e.id
    WHERE e.escalation_reason != 'no_escalation'
    ORDER BY e.created_at DESC
    LIMIT 100
""")


@router.get("/cases", response_model=list[EscalationCaseRead])
async def list_cases(db: AsyncSession = Depends(get_db)) -> list[EscalationCaseRead]:
    result = await db.execute(_CASES_SQL)
    rows = result.fetchall()
    return [
        EscalationCaseRead(
            id=row.id,
            event_id=row.event_id,
            content=row.content,
            category=row.category,
            escalation_reason=row.escalation_reason,
            confidence_max=float(row.confidence_max) if row.confidence_max is not None else None,
            created_at=row.created_at,
            action=row.action,
            notes=row.notes,
        )
        for row in rows
    ]


@router.post("/cases/{escalation_id}/decide", response_model=CaseDecisionRead, status_code=201)
async def create_decision(
    escalation_id: str,
    body: CaseDecisionCreate,
    db: AsyncSession = Depends(get_db),
) -> CaseDecisionRead:
    esc_result = await db.execute(
        text("SELECT id FROM escalations WHERE id = :id"),
        {"id": escalation_id},
    )
    if esc_result.fetchone() is None:
        raise HTTPException(status_code=404, detail=f"Escalation {escalation_id!r} not found")

    existing = await db.execute(
        text("SELECT id FROM case_decisions WHERE escalation_id = :eid"),
        {"eid": escalation_id},
    )
    if existing.fetchone() is not None:
        raise HTTPException(status_code=409, detail="Decision already exists for this escalation")

    now = datetime.now(UTC)
    decision = CaseDecision(
        id=str(uuid.uuid4()),
        escalation_id=escalation_id,
        action=body.action,
        notes=body.notes,
        created_at=now,
    )
    db.add(decision)
    await db.commit()
    logger.info("Decision %s recorded for escalation %s", body.action, escalation_id)

    return CaseDecisionRead(
        id=decision.id,
        escalation_id=decision.escalation_id,
        action=decision.action,
        notes=decision.notes,
        created_at=decision.created_at,
    )
