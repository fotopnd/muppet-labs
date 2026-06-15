from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from year_zero.api.schemas import BatchAccepted, BatchDecisionsRequest
from year_zero.database import get_db
from year_zero.models import GameSession, PlayerDecision

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.post("/batch", response_model=BatchAccepted, status_code=201)
async def batch_decisions(
    request: Request,
    body: BatchDecisionsRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchAccepted:
    session = await db.get(GameSession, body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    rows = [
        PlayerDecision(
            session_id=body.session_id,
            document_id=d.document_id,
            agent_condition=d.agent_condition,
            player_verdict=d.player_verdict,
            player_correct=d.player_correct,
            latency_ms=d.latency_ms,
            agreed_with_agent=d.agreed_with_agent,
            bar_public_trust=d.bars.get("public_trust", 0),
            bar_security=d.bars.get("security", 0),
            bar_treasury=d.bars.get("treasury", 0),
            bar_legitimacy=d.bars.get("legitimacy", 0),
            bar_compliance=d.bars.get("compliance", 0),
            game_day=d.game_day,
            phase=d.phase,
            category_tier=d.category_tier,
            is_calibration=d.is_calibration,
        )
        for d in body.decisions
    ]
    db.add_all(rows)
    await db.commit()

    # Broadcast refresh to all SSE subscribers
    queues = list(request.app.state.sse_queues)
    for q in queues:
        await q.put("refresh")

    logger.info(
        "Batch inserted: session=%d day=%d count=%d", body.session_id, body.game_day, len(rows)
    )
    return BatchAccepted(accepted=len(rows))
