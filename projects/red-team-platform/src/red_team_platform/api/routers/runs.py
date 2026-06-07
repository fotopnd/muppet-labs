from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.api.deps import get_db
from red_team_platform.api.schemas import RunListOut, RunOut, SampleOut
from red_team_platform.models import Attack, Run

router = APIRouter(tags=["runs"])


@router.get("/runs", response_model=RunListOut)
async def list_runs(
    session_id: uuid.UUID | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    db: AsyncSession = Depends(get_db),
) -> RunListOut:
    base = select(Run)
    if session_id:
        base = base.where(Run.session_id == session_id)

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar_one()

    result = await db.execute(
        base.order_by(Run.created_at.desc()).limit(page_size).offset((page - 1) * page_size)
    )
    runs = result.scalars().all()

    # Fetch joined attack data
    items: list[RunOut] = []
    for run in runs:
        atk_result = await db.execute(select(Attack).where(Attack.id == run.attack_id))
        atk = atk_result.scalar_one()
        items.append(
            RunOut(
                id=run.id,
                session_id=run.session_id,
                attack_id=run.attack_id,
                model_name=run.model_name,
                response_text=run.response_text,
                jailbreak_success=run.jailbreak_success,
                classifier_score=run.classifier_score,
                latency_ms=run.latency_ms,
                created_at=run.created_at,
                harm_category=atk.harm_category,
                strategy=atk.strategy,
                attack_text=atk.attack_text,
            )
        )

    return RunListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/sample/{run_id}", response_model=SampleOut)
async def get_sample(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> SampleOut:
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    atk_result = await db.execute(select(Attack).where(Attack.id == run.attack_id))
    atk = atk_result.scalar_one()

    return SampleOut(
        run_id=run.id,
        attack_text=atk.attack_text,
        response_text=run.response_text,
        harm_category=atk.harm_category,
        strategy=atk.strategy,
        jailbreak_success=run.jailbreak_success,
        classifier_score=run.classifier_score,
        latency_ms=run.latency_ms,
        model_name=run.model_name,
        session_id=run.session_id,
        created_at=run.created_at,
    )
