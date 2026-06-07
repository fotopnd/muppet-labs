from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from error_hide_seek.api.deps import get_db
from error_hide_seek.api.schemas import ReviewConfirmOut, ReviewSubmit
from error_hide_seek.models import (
    Condition,
    HumanDetection,
    PlantedError,
    ReviewSession,
    SessionStatus,
)
from error_hide_seek.scoring.scorer import is_true_positive

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewConfirmOut, status_code=201)
async def submit_review(body: ReviewSubmit, db: AsyncSession = Depends(get_db)) -> ReviewConfirmOut:
    session_row = await db.get(ReviewSession, body.session_id)
    if session_row is None:
        raise HTTPException(404, "Session not found")
    if session_row.status == SessionStatus.COMPLETED:
        raise HTTPException(409, "Already submitted")
    if session_row.condition == Condition.AGENT_ONLY:
        raise HTTPException(422, "Cannot submit human review for agent_only session")

    pe = await db.scalar(
        select(PlantedError).where(
            PlantedError.paper_id == session_row.paper_id,
            PlantedError.experiment_id == session_row.experiment_id,
        )
    )
    if pe is None:
        raise HTTPException(500, "Planted error missing for session")

    for det in body.detections:
        tp = is_true_positive(det.text_excerpt, pe.original_text)
        db.add(
            HumanDetection(
                review_session_id=body.session_id,
                text_excerpt=det.text_excerpt,
                note=det.note,
                is_true_positive=tp,
            )
        )

    session_row.status = SessionStatus.COMPLETED
    session_row.completed_at = datetime.now(UTC)
    await db.commit()
    return ReviewConfirmOut(session_id=body.session_id, status="completed")
