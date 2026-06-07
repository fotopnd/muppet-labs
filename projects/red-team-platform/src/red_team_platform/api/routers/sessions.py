from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.api.deps import get_db
from red_team_platform.api.schemas import SessionOut
from red_team_platform.models import RunSession

router = APIRouter(tags=["sessions"])


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(db: AsyncSession = Depends(get_db)) -> list[SessionOut]:
    result = await db.execute(select(RunSession).order_by(RunSession.created_at.desc()))
    sessions = result.scalars().all()
    return [SessionOut.model_validate(s) for s in sessions]
