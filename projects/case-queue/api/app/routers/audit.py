from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Action, Decision
from app.schemas import AuditEntry, Page

router = APIRouter(tags=["audit"])

_AUDIT_SORT_COLUMNS = {
    "created_at": Decision.created_at,
    "action": Decision.action,
    "actor_id": Decision.actor_id,
}


@router.get("/audit-log/actors", response_model=list[str])
async def get_audit_actors(db: AsyncSession = Depends(get_db)) -> list[str]:
    result = await db.execute(
        select(Decision.actor_id).distinct().order_by(Decision.actor_id)
    )
    return list(result.scalars().all())


@router.get("/audit-log", response_model=Page[AuditEntry])
async def get_audit_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    case_id: str | None = None,
    actor_id: str | None = None,
    action: Action | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort_by: str | None = Query(None, pattern="^(created_at|action|actor_id)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
) -> Page[AuditEntry]:
    filters = _build_filters(case_id, actor_id, action, date_from, date_to)

    total_result = await db.execute(
        select(func.count()).select_from(Decision).where(*filters)
    )
    total = total_result.scalar_one()

    col = _AUDIT_SORT_COLUMNS.get(sort_by or "created_at", Decision.created_at)
    order_expr = asc(col) if sort_dir == "asc" else desc(col)

    offset = (page - 1) * page_size
    items_result = await db.execute(
        select(Decision)
        .where(*filters)
        .order_by(order_expr)
        .offset(offset)
        .limit(page_size)
    )
    items = list(items_result.scalars().all())

    return Page(items=items, total=total, page=page, page_size=page_size)


def _build_filters(
    case_id: str | None,
    actor_id: str | None,
    action: Action | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> list:
    filters = []
    if case_id is not None:
        filters.append(Decision.case_id == case_id)
    if actor_id is not None:
        filters.append(Decision.actor_id == actor_id)
    if action is not None:
        filters.append(Decision.action == action)
    if date_from is not None:
        filters.append(Decision.created_at >= date_from)
    if date_to is not None:
        filters.append(Decision.created_at <= date_to)
    return filters
