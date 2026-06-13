from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.api.deps import get_db
from red_team_platform.api.schemas import (
    AttackListOut,
    AttackOut,
    AttackSummaryOut,
    FilterValuesOut,
)
from red_team_platform.models import Attack

router = APIRouter(prefix="/attacks", tags=["attacks"])


@router.get("/summary", response_model=AttackSummaryOut)
async def get_attack_summary(
    source: str | None = None,
    harm_category: str | None = None,
    strategy: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> AttackSummaryOut:
    def _apply(q: select) -> select:
        if source:
            q = q.where(Attack.source == source)
        if harm_category:
            q = q.where(Attack.harm_category == harm_category)
        if strategy:
            q = q.where(Attack.strategy == strategy)
        return q

    total_res = await db.execute(
        _apply(select(func.count()).select_from(Attack))
    )
    total = total_res.scalar_one()

    top_cat: str | None = None
    top_strat: str | None = None

    if total > 0:
        cat_res = await db.execute(
            _apply(
                select(Attack.harm_category)
                .group_by(Attack.harm_category)
                .order_by(func.count(Attack.id).desc())
                .limit(1)
            )
        )
        top_cat = cat_res.scalar_one_or_none()

        strat_res = await db.execute(
            _apply(
                select(Attack.strategy)
                .group_by(Attack.strategy)
                .order_by(func.count(Attack.id).desc())
                .limit(1)
            )
        )
        top_strat = strat_res.scalar_one_or_none()

    return AttackSummaryOut(total=total, top_category=top_cat, top_strategy=top_strat)


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
