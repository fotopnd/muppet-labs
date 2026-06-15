from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.api.deps import get_db
from red_team_platform.api.schemas import AuditLogEntryOut, AuditLogOut
from red_team_platform.models import AuditLogEntry

router = APIRouter(tags=["audit"])


@router.get("/audit-log", response_model=AuditLogOut)
async def list_audit_log(
    decision: str | None = None,
    reviewer: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
) -> AuditLogOut:
    """Return paginated audit log entries, filterable by decision and reviewer."""
    base = select(AuditLogEntry)

    # ORM .where() chains — never text() with nullable params (asyncpg NULL rule)
    if decision:
        base = base.where(AuditLogEntry.decision == decision)
    if reviewer:
        base = base.where(AuditLogEntry.reviewer == reviewer)

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar_one()

    result = await db.execute(
        base.order_by(AuditLogEntry.created_at.desc()).limit(limit).offset(offset)
    )
    entries = result.scalars().all()

    return AuditLogOut(
        items=[AuditLogEntryOut.model_validate(e) for e in entries],
        total=total,
        limit=limit,
        offset=offset,
    )
