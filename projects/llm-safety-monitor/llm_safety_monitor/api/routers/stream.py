from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from llm_safety_monitor.api.database import get_db
from llm_safety_monitor.api.models import ClassificationResult, Interaction
from llm_safety_monitor.api.schemas import RecentEvent, StreamResponse, VerdictEntry

router = APIRouter(prefix="/stream", tags=["stream"])


@router.get("/recent", response_model=StreamResponse)
async def get_recent(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> StreamResponse:
    """Return the most recent N interactions with per-model verdicts."""
    result = await db.execute(
        select(Interaction).order_by(Interaction.created_at.desc()).limit(limit)
    )
    interactions = result.scalars().all()

    if not interactions:
        return StreamResponse(events=[])

    event_ids = [i.id for i in interactions]

    clf_result = await db.execute(
        select(ClassificationResult).where(ClassificationResult.event_id.in_(event_ids))
    )
    classifications = clf_result.scalars().all()

    verdicts_by_event: dict[UUID, list[VerdictEntry]] = defaultdict(list)
    for clf in classifications:
        if clf.event_id is not None:
            verdicts_by_event[clf.event_id].append(
                VerdictEntry(
                    model_name=clf.model_name,
                    predicted_label=clf.predicted_label,
                    confidence=clf.confidence,
                    taxonomy_labels=clf.taxonomy_labels,
                )
            )

    events = [
        RecentEvent(
            event_id=interaction.id,
            prompt_text=(interaction.prompt_text or "")[:200],
            response_text=(interaction.response_text or None) and interaction.response_text[:200],
            source_dataset=interaction.source_dataset,
            verdicts=verdicts_by_event.get(interaction.id, []),
            escalation_reason=interaction.escalation_reason,
        )
        for interaction in interactions
    ]
    return StreamResponse(events=events)
