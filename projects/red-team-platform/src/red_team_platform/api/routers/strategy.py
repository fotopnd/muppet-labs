from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.api.deps import get_db
from red_team_platform.api.schemas import StrategyBar, StrategyComparisonOut
from red_team_platform.models import Attack, Run

router = APIRouter(tags=["strategy"])


@router.get("/strategy-comparison", response_model=StrategyComparisonOut)
async def get_strategy_comparison(db: AsyncSession = Depends(get_db)) -> StrategyComparisonOut:
    result = await db.execute(
        select(
            Attack.strategy,
            func.count().label("total_runs"),
            func.sum(case((Run.jailbreak_success == True, 1), else_=0)).label("total_successes"),  # noqa: E712
        )
        .join(Attack, Run.attack_id == Attack.id)
        .group_by(Attack.strategy)
    )
    rows = result.all()
    bars = [
        StrategyBar(
            strategy=row.strategy,
            total_runs=row.total_runs,
            total_successes=int(row.total_successes or 0),
            asr=int(row.total_successes or 0) / row.total_runs if row.total_runs > 0 else 0.0,
        )
        for row in rows
    ]
    bars.sort(key=lambda b: b.asr, reverse=True)
    return StrategyComparisonOut(bars=bars)
