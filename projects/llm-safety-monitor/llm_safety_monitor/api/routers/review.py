from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from llm_safety_monitor.api.database import get_db
from llm_safety_monitor.api.schemas import DisagreementSample, DisagreementsResponse

router = APIRouter(prefix="/cases", tags=["review"])


@router.get("", response_model=DisagreementsResponse)
async def get_escalated_cases(db: AsyncSession = Depends(get_db)) -> DisagreementsResponse:
    """Return escalated events for human review."""
    rows = (
        await db.execute(
            text("""
                SELECT i.id, i.prompt_text, i.escalation_reason,
                       pair_c.predicted_label,
                       tax_c.taxonomy_labels
                FROM interactions i
                LEFT JOIN classifications pair_c
                    ON pair_c.event_id = i.id AND pair_c.model_name = 'pair_classifier'
                LEFT JOIN classifications tax_c
                    ON tax_c.event_id = i.id AND tax_c.model_name = 'taxonomy_classifier'
                WHERE i.escalation_reason IS NOT NULL
                  AND i.escalation_reason != 'LOG_ONLY'
                ORDER BY i.created_at DESC
                LIMIT 100
            """)
        )
    ).fetchall()

    total_row = await db.execute(
        text("""
            SELECT COUNT(*) FROM interactions
            WHERE escalation_reason IS NOT NULL AND escalation_reason != 'LOG_ONLY'
        """)
    )
    total = total_row.scalar() or 0

    samples = [
        DisagreementSample(
            event_id=row[0],
            prompt_text=(row[1] or "")[:200],
            escalation_reason=row[2],
            pair_label=row[3],
            taxonomy_labels=row[4] or [],
        )
        for row in rows
    ]
    return DisagreementsResponse(total=total, samples=samples)
