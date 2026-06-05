from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from moderation_dashboard.api.database import get_db

router = APIRouter(tags=["admin"])
logger = logging.getLogger(__name__)


@router.post("/admin/restart", status_code=204)
async def restart_stream(db: AsyncSession = Depends(get_db)) -> None:
    """Truncate all live (non-seeded) classifications and anomaly flags.

    Seeded rows (seeded=true) are preserved so historical model metrics remain visible.
    The looping producer continues its current cycle; on the next loop pass, new live
    events accumulate from a clean baseline.
    """
    await db.execute(text("DELETE FROM classifications WHERE seeded = false"))
    await db.execute(text("DELETE FROM anomaly_flags"))
    await db.commit()
    logger.info("Stream restarted — live classifications and anomaly flags cleared")
