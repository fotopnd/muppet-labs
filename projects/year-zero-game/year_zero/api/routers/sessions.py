from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from year_zero.api.schemas import CreateSessionRequest, PatchSessionRequest, SessionCreated
from year_zero.database import get_db
from year_zero.models import GameSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionCreated, status_code=201)
async def create_session(
    body: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionCreated:
    session = GameSession(started_at=body.started_at)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    logger.info("Session created: id=%d", session.id)
    return SessionCreated(session_id=session.id)


@router.patch("/{session_id}", status_code=200)
async def patch_session(
    session_id: int,
    body: PatchSessionRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    session = await db.get(GameSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    session.ended_at = body.ended_at
    session.total_days = body.total_days
    session.total_decisions = body.total_decisions
    session.correct_decisions = body.correct_decisions
    session.accuracy = body.accuracy
    session.phase_reached = body.phase_reached
    session.game_over_condition = body.game_over_condition
    session.final_bar_public_trust = body.final_bars.get("public_trust")
    session.final_bar_security = body.final_bars.get("security")
    session.final_bar_treasury = body.final_bars.get("treasury")
    session.final_bar_legitimacy = body.final_bars.get("legitimacy")
    session.final_bar_compliance = body.final_bars.get("compliance")
    session.total_agreements = body.compliance_profile.get("total_agreements")
    session.total_overrides = body.compliance_profile.get("total_overrides")
    session.total_no_agent_decisions = body.compliance_profile.get("total_no_agent_decisions")
    session.agreement_rate = body.compliance_profile.get("agreement_rate")
    session.correct_agreements = body.compliance_profile.get("correct_agreements")
    session.correct_overrides = body.compliance_profile.get("correct_overrides")
    session.correct_no_agent = body.compliance_profile.get("correct_no_agent")
    session.calibration_accuracy = body.calibration_accuracy
    session.calibration_decisions = body.calibration_decisions
    session.category_tiers = body.category_tiers

    await db.commit()
    logger.info("Session patched: id=%d condition=%s", session_id, body.game_over_condition)
    return {"ok": True}
