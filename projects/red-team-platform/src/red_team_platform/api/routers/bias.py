from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.api.deps import get_db
from red_team_platform.api.schemas import BiasScoreRow, BiasScoresOut

router = APIRouter(tags=["bias"])


@router.get("/bias/scores", response_model=BiasScoresOut)
async def get_bias_scores(db: AsyncSession = Depends(get_db)) -> BiasScoresOut:
    rows_result = await db.execute(
        text("""
            SELECT
                bp.topic_id,
                bp.government,
                bp.label,
                MAX(CASE WHEN bds.language = 'zh' THEN bds.cosine_distance END) AS zh_score,
                MAX(CASE WHEN bds.language = 'ru' THEN bds.cosine_distance END) AS ru_score,
                MAX(CASE WHEN bds.language = 'ar' THEN bds.cosine_distance END) AS ar_score
            FROM bias_probes bp
            LEFT JOIN bias_divergence_scores bds ON bp.id = bds.probe_id
            GROUP BY bp.topic_id, bp.government, bp.label
            ORDER BY bp.government, bp.topic_id
        """)
    )
    rows = [
        BiasScoreRow(
            topic_id=row.topic_id,
            government=row.government,
            label=row.label,
            zh_score=row.zh_score,
            ru_score=row.ru_score,
            ar_score=row.ar_score,
        )
        for row in rows_result.mappings()
    ]

    # Most recent model name from any divergence score
    model_result = await db.execute(
        text("SELECT model_name FROM bias_divergence_scores ORDER BY created_at DESC LIMIT 1")
    )
    model_row = model_result.fetchone()
    scored_model = model_row[0] if model_row else None

    return BiasScoresOut(rows=rows, scored_model=scored_model)
