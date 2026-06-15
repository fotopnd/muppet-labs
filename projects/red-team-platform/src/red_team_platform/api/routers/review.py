from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.api.deps import get_db
from red_team_platform.api.schemas import CaseReviewCreate, CaseReviewOut
from red_team_platform.models import AuditLogEntry, CaseReview, Run

router = APIRouter(tags=["review"])


@router.post("/runs/{run_id}/review", response_model=CaseReviewOut)
async def submit_review(
    run_id: uuid.UUID,
    body: CaseReviewCreate,
    db: AsyncSession = Depends(get_db),
) -> CaseReviewOut:
    """Upsert a review decision for a run. Also appends an audit log entry."""
    # Verify run exists
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    # Check for existing decision
    existing_result = await db.execute(select(CaseReview).where(CaseReview.run_id == run_id))
    existing = existing_result.scalar_one_or_none()

    if existing is not None:
        # Update existing decision
        existing.decision = body.decision
        existing.reason = body.reason
        existing.reviewed_at = datetime.now(UTC)
        existing.reviewer = body.reviewer
        action = "review_updated"
        review = existing
    else:
        # Create new decision
        review = CaseReview(
            run_id=run_id,
            decision=body.decision,
            reason=body.reason,
            reviewer=body.reviewer,
        )
        db.add(review)
        action = "review_created"

    # Append audit log entry (append-only — never update)
    audit_entry = AuditLogEntry(
        run_id=run_id,
        action=action,
        decision=body.decision,
        reason=body.reason,
        reviewer=body.reviewer,
    )
    db.add(audit_entry)

    await db.commit()
    await db.refresh(review)
    return CaseReviewOut.model_validate(review)


@router.get("/runs/{run_id}/review", response_model=CaseReviewOut)
async def get_review(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CaseReviewOut:
    """Get the current review decision for a run. Returns 404 if none exists."""
    result = await db.execute(select(CaseReview).where(CaseReview.run_id == run_id))
    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=404, detail="No review decision for this run")
    return CaseReviewOut.model_validate(review)
