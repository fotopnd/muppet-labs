from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gridiron.api.schemas import ScheduleGame, WeekSchedule
from gridiron.database import get_db

router = APIRouter()

_WEEK_QUERY = text("""
    SELECT g.id AS game_id, g.week, g.broadcast_slot, g.status,
           g.home_score, g.away_score,
           g.home_program_id, hp.name AS home_name, hp.emoji AS home_emoji,
           g.away_program_id, ap.name AS away_name, ap.emoji AS away_emoji
    FROM games g
    JOIN programs hp ON hp.id = g.home_program_id
    JOIN programs ap ON ap.id = g.away_program_id
    WHERE g.week = :week AND g.season = 1
    ORDER BY g.broadcast_slot, g.id
""")


@router.get("/schedule/current", response_model=WeekSchedule)
async def current_schedule(db: AsyncSession = Depends(get_db)) -> WeekSchedule:
    week = (
        await db.execute(
            text("SELECT MIN(week) FROM games WHERE status IN ('live','scheduled') AND season=1")
        )
    ).scalar()
    if week is None:
        raise HTTPException(status_code=404, detail="No active week")
    rows = (await db.execute(_WEEK_QUERY, {"week": week})).mappings().all()
    return WeekSchedule(week=week, games=[ScheduleGame.model_validate(dict(r)) for r in rows])


@router.get("/schedule/week/{week}", response_model=WeekSchedule)
async def week_schedule(week: int, db: AsyncSession = Depends(get_db)) -> WeekSchedule:
    rows = (await db.execute(_WEEK_QUERY, {"week": week})).mappings().all()
    return WeekSchedule(week=week, games=[ScheduleGame.model_validate(dict(r)) for r in rows])
