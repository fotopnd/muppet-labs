from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.api.deps import get_db
from red_team_platform.api.schemas import AttackListOut, AttackOut, FilterValuesOut
from red_team_platform.models import Attack

router = APIRouter(prefix="/attacks", tags=["attacks"])


@router.get("", response_model=AttackListOut)
async def list_attacks(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    source: str | None = None,
    harm_category: str | None = None,
    strategy: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> AttackListOut:
    base = select(Attack)
    if source:
        base = base.where(Attack.source == source)
    if harm_category:
        base = base.where(Attack.harm_category == harm_category)
    if strategy:
        base = base.where(Attack.strategy == strategy)

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar_one()

    items_result = await db.execute(
        base.order_by(Attack.created_at.desc()).limit(page_size).offset((page - 1) * page_size)
    )
    items = items_result.scalars().all()

    return AttackListOut(
        items=[AttackOut.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/harm-categories", response_model=FilterValuesOut)
async def list_harm_categories(db: AsyncSession = Depends(get_db)) -> FilterValuesOut:
    result = await db.execute(
        select(Attack.harm_category).distinct().order_by(Attack.harm_category)
    )
    return FilterValuesOut(values=[row[0] for row in result])


@router.get("/strategies", response_model=FilterValuesOut)
async def list_strategies(db: AsyncSession = Depends(get_db)) -> FilterValuesOut:
    result = await db.execute(select(Attack.strategy).distinct().order_by(Attack.strategy))
    return FilterValuesOut(values=[row[0] for row in result])
