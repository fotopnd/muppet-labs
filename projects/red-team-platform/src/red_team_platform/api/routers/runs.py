from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.api.deps import get_db
from red_team_platform.api.schemas import RunListOut, RunOut, SampleOut, TopFailureOut, TopFailuresOut
from red_team_platform.models import Attack, Run

router = APIRouter(tags=["runs"])

_DEDUP_SQL = text("""
    SELECT DISTINCT ON (r.attack_id)
        r.id,
        r.session_id,
        r.attack_id,
        r.model_name,
        r.response_text,
        r.jailbreak_success,
        r.classifier_score,
        r.latency_ms,
        r.created_at,
        a.harm_category,
        a.strategy,
        a.attack_text
    FROM runs r
    JOIN attacks a ON a.id = r.attack_id
    WHERE r.session_id = :session_id
    ORDER BY r.attack_id, r.created_at DESC
""")


@router.get("/runs", response_model=RunListOut)
async def list_runs(
    session_id: uuid.UUID | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    dedup: bool = False,
    db: AsyncSession = Depends(get_db),
) -> RunListOut:
    if dedup:
        if session_id is None:
            raise HTTPException(status_code=400, detail="session_id required when dedup=true")
        result = await db.execute(_DEDUP_SQL, {"session_id": str(session_id)})
        rows = result.mappings().all()
        items = [
            RunOut(
                id=row["id"],
                session_id=row["session_id"],
                attack_id=row["attack_id"],
                model_name=row["model_name"],
                response_text=row["response_text"],
                jailbreak_success=row["jailbreak_success"],
                classifier_score=row["classifier_score"],
                latency_ms=row["latency_ms"],
                created_at=row["created_at"],
                harm_category=row["harm_category"],
                strategy=row["strategy"],
                attack_text=row["attack_text"],
            )
            for row in rows
        ]
        return RunListOut(items=items, total=len(items), page=1, page_size=len(items))

    base = select(Run)
    if session_id:
        base = base.where(Run.session_id == session_id)

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar_one()

    result = await db.execute(
        base.order_by(Run.created_at.desc()).limit(page_size).offset((page - 1) * page_size)
    )
    runs = result.scalars().all()

    items_out: list[RunOut] = []
    for run in runs:
        atk_result = await db.execute(select(Attack).where(Attack.id == run.attack_id))
        atk = atk_result.scalar_one()
        items_out.append(
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

    return RunListOut(items=items_out, total=total, page=page, page_size=page_size)


@router.get("/top-failures", response_model=TopFailuresOut)
async def top_failures(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    db: AsyncSession = Depends(get_db),
) -> TopFailuresOut:
    result = await db.execute(
        select(
            Run.id,
            Run.classifier_score,
            Run.response_text,
            Run.model_name,
            Attack.strategy,
            Attack.harm_category,
            Attack.attack_text,
        )
        .join(Attack, Run.attack_id == Attack.id)
        .where(Run.jailbreak_success == True)  # noqa: E712
        .order_by(Run.classifier_score.desc())
        .limit(limit)
    )
    rows = result.mappings().all()
    return TopFailuresOut(
        items=[
            TopFailureOut(
                run_id=row["id"],
                strategy=row["strategy"],
                harm_category=row["harm_category"],
                model_name=row["model_name"],
                classifier_score=row["classifier_score"],
                attack_text=row["attack_text"],
                response_text=row["response_text"],
            )
            for row in rows
        ]
    )


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
