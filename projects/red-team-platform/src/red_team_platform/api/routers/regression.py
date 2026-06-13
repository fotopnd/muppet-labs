from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.api.deps import get_db
from red_team_platform.api.schemas import (
    CategoryDeltaItem,
    CategoryDeltaOut,
    RegressionOut,
    RegressionPoint,
)
from red_team_platform.models import RunSession

router = APIRouter(tags=["regression"])

_CATEGORY_ASR_SQL = text("""
    SELECT
        a.harm_category,
        SUM(r.jailbreak_success::int)::float / NULLIF(COUNT(r.id), 0) AS asr
    FROM runs r
    JOIN attacks a ON r.attack_id = a.id
    WHERE r.session_id = :session_id
    GROUP BY a.harm_category
""")


@router.get("/regression", response_model=RegressionOut)
async def get_regression(db: AsyncSession = Depends(get_db)) -> RegressionOut:
    result = await db.execute(select(RunSession).order_by(RunSession.created_at.asc()))
    sessions = result.scalars().all()
    points = [
        RegressionPoint(
            session_id=s.id,
            model_name=s.model_name,
            asr=s.asr,
            total_attacks=s.total_attacks,
            created_at=s.created_at,
        )
        for s in sessions
    ]
    model_names = sorted({p.model_name for p in points})
    return RegressionOut(points=points, model_names=model_names)


@router.get("/regression/category-delta", response_model=CategoryDeltaOut)
async def get_category_delta(
    model: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> CategoryDeltaOut:
    base = select(RunSession)
    if model:
        base = base.where(RunSession.model_name == model)

    baseline_q = base.order_by(RunSession.created_at.asc()).limit(1)
    baseline_row = (await db.execute(baseline_q)).scalars().first()
    if baseline_row is None:
        return CategoryDeltaOut(
            items=[], baseline_session_id=None, latest_session_id=None, model_name=None
        )

    resolved_model = baseline_row.model_name
    latest_q = (
        select(RunSession)
        .where(RunSession.model_name == resolved_model)
        .order_by(RunSession.created_at.desc())
        .limit(1)
    )
    latest_row = (await db.execute(latest_q)).scalars().first()

    if latest_row is None or latest_row.id == baseline_row.id:
        return CategoryDeltaOut(
            items=[],
            baseline_session_id=baseline_row.id,
            latest_session_id=baseline_row.id,
            model_name=resolved_model,
        )

    baseline_result = await db.execute(_CATEGORY_ASR_SQL, {"session_id": str(baseline_row.id)})
    latest_result = await db.execute(_CATEGORY_ASR_SQL, {"session_id": str(latest_row.id)})

    baseline_map = {row["harm_category"]: row["asr"] for row in baseline_result.mappings()}
    latest_map = {row["harm_category"]: row["asr"] for row in latest_result.mappings()}

    all_cats = sorted(set(baseline_map) | set(latest_map))
    items = [
        CategoryDeltaItem(
            harm_category=cat,
            baseline_asr=baseline_map.get(cat, 0.0),
            latest_asr=latest_map.get(cat, 0.0),
            delta=latest_map.get(cat, 0.0) - baseline_map.get(cat, 0.0),
        )
        for cat in all_cats
    ]

    return CategoryDeltaOut(
        items=items,
        baseline_session_id=baseline_row.id,
        latest_session_id=latest_row.id,
        model_name=resolved_model,
    )
