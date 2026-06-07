from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.api.deps import get_db
from red_team_platform.api.schemas import CoverageCell, CoverageOut

router = APIRouter(tags=["coverage"])


@router.get("/coverage", response_model=CoverageOut)
async def get_coverage(db: AsyncSession = Depends(get_db)) -> CoverageOut:
    result = await db.execute(
        text(
            "SELECT harm_category, strategy, total_runs, total_successes, asr "
            "FROM coverage_summary ORDER BY harm_category, strategy"
        )
    )
    rows = result.mappings().all()
    cells = [CoverageCell(**dict(row)) for row in rows]
    harm_categories = sorted({c.harm_category for c in cells})
    strategies = sorted({c.strategy for c in cells})
    return CoverageOut(cells=cells, harm_categories=harm_categories, strategies=strategies)
