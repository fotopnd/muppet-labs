from __future__ import annotations

import json
import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from year_zero.api.schemas import CardOut
from year_zero.database import get_db
from year_zero.models import DocumentLibrary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cards", tags=["cards"])

AgentCondition = Literal["none", "tier_1", "tier_2", "tier_3"]


def assign_condition(doc: DocumentLibrary) -> AgentCondition:
    """
    Returns the agent_condition to assign for this document on this serve.
    Picks the condition most under-served relative to target_condition_mix.
    """
    served: dict[str, int] = {
        "none": doc.served_none,
        "tier_1": doc.served_tier_1,
        "tier_2": doc.served_tier_2,
        "tier_3": doc.served_tier_3,
    }
    target: dict[str, float] = doc.target_condition_mix
    total = sum(served.values()) or 1
    deficit = {c: target.get(c, 0.0) - (served[c] / total) for c in target}
    return max(deficit, key=lambda c: deficit[c])  # type: ignore[return-value]


def _to_card_out(doc: DocumentLibrary, condition: AgentCondition) -> CardOut:
    return CardOut(
        id=doc.id,
        document_text=doc.document_text,
        harm_category=doc.harm_category,
        phase=doc.phase,
        generation_tier=doc.generation_tier,
        is_harmful=doc.is_harmful,
        gork_verdict=doc.gork_verdict,
        gork_confidence=doc.gork_confidence,
        gork_reasoning=doc.gork_reasoning,
        agent_condition=condition,
    )


@router.get("/calibration", response_model=list[CardOut])
async def get_calibration_cards(db: AsyncSession = Depends(get_db)) -> list[CardOut]:
    result = await db.execute(
        select(DocumentLibrary)
        .where(DocumentLibrary.is_calibration.is_(True))
        .limit(10)
    )
    docs = list(result.scalars().all())
    if not docs:
        raise HTTPException(status_code=404, detail="No calibration cards found")

    cards: list[CardOut] = []
    for doc in docs:
        condition = assign_condition(doc)
        if condition == "none":
            inc = {"served_none": DocumentLibrary.served_none + 1}
        elif condition == "tier_1":
            inc = {"served_tier_1": DocumentLibrary.served_tier_1 + 1}
        elif condition == "tier_2":
            inc = {"served_tier_2": DocumentLibrary.served_tier_2 + 1}
        else:
            inc = {"served_tier_3": DocumentLibrary.served_tier_3 + 1}
        await db.execute(update(DocumentLibrary).where(DocumentLibrary.id == doc.id).values(**inc))
        cards.append(_to_card_out(doc, condition))
    await db.commit()

    logger.info("Calibration cards served: count=%d", len(cards))
    return cards


@router.get("/phase/{phase}", response_model=list[CardOut])
async def get_phase_cards(
    phase: int,
    category_tiers: str = "{}",
    db: AsyncSession = Depends(get_db),
) -> list[CardOut]:
    if phase not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="Phase must be 1, 2, or 3")

    try:
        _tiers: dict[str, int] = json.loads(category_tiers)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="category_tiers must be valid JSON") from exc

    result = await db.execute(
        select(DocumentLibrary)
        .where(DocumentLibrary.phase == phase)
        .where(DocumentLibrary.is_calibration.is_(False))
    )
    docs = list(result.scalars().all())
    if not docs:
        raise HTTPException(status_code=404, detail=f"No cards found for phase {phase}")

    cards: list[CardOut] = []
    for doc in docs:
        condition = assign_condition(doc)
        # Atomic SQL increment — safe under concurrent serves
        if condition == "none":
            inc = {"served_none": DocumentLibrary.served_none + 1}
        elif condition == "tier_1":
            inc = {"served_tier_1": DocumentLibrary.served_tier_1 + 1}
        elif condition == "tier_2":
            inc = {"served_tier_2": DocumentLibrary.served_tier_2 + 1}
        else:
            inc = {"served_tier_3": DocumentLibrary.served_tier_3 + 1}
        await db.execute(update(DocumentLibrary).where(DocumentLibrary.id == doc.id).values(**inc))
        cards.append(_to_card_out(doc, condition))

    await db.commit()
    logger.info("Phase cards served: phase=%d count=%d", phase, len(cards))
    return cards
