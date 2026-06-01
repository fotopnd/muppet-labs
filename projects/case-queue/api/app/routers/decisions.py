from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import Actor, get_actor
from app.models import ACTION_TO_STATUS, Action, ActorRole, Case, Decision
from app.schemas import DecisionCreate, DecisionRead

router = APIRouter(tags=["decisions"])


@router.post("/cases/{case_id}/decisions", response_model=DecisionRead, status_code=201)
async def create_decision(
    case_id: str,
    body: DecisionCreate,
    actor: Actor = Depends(get_actor),
    db: AsyncSession = Depends(get_db),
) -> DecisionRead:
    case_result = await db.execute(select(Case).where(Case.id == case_id))
    if case_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail=f"Case {case_id!r} not found")

    if actor.role == ActorRole.reviewer and body.action == Action.escalate:
        raise HTTPException(
            status_code=403, detail="Role 'reviewer' cannot escalate cases"
        )

    now = datetime.now(UTC)
    decision = Decision(
        id=str(uuid.uuid4()),
        case_id=case_id,
        actor_id=actor.id,
        actor_role=actor.role,
        action=body.action,
        notes=body.notes,
        created_at=now,
    )
    db.add(decision)

    await db.execute(
        update(Case)
        .where(Case.id == case_id)
        .values(status=ACTION_TO_STATUS[body.action], updated_at=now)
    )

    await db.flush()
    await db.refresh(decision)
    return decision  # type: ignore[return-value]
