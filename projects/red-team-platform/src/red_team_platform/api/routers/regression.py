from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.api.deps import get_db
from red_team_platform.api.schemas import RegressionOut, RegressionPoint
from red_team_platform.models import RunSession

router = APIRouter(tags=["regression"])


@router.get("/regression", response_model=RegressionOut)
async def get_regression(db: AsyncSession = Depends(get_db)) -> RegressionOut:
    result = await db.execute(select(RunSession).order_by(RunSession.created_at.asc()))
    sessions = result.scalars().all()
    points = [
        RegressionPoint(
            session_id=s.id,
            model_name=s.model_name,
            asr=s.asr,
            total_attacks=s.total_attacks,
            created_at=s.created_at,
        )
        for s in sessions
    ]
    model_names = sorted({p.model_name for p in points})
    return RegressionOut(points=points, model_names=model_names)
