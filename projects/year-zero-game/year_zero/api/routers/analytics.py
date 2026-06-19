from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import Float, case, cast, func, select

from year_zero.api.schemas import AnalyticsSummary
from year_zero.models import DocumentLibrary, GameSession, PlayerDecision

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


async def _compute_summary(request: Request) -> AnalyticsSummary:
    async with request.app.state.session_factory() as db:
        from datetime import UTC, datetime
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        # Session counts
        total_sessions: int = (await db.execute(
            select(func.count()).select_from(GameSession).where(GameSession.ended_at.isnot(None))
        )).scalar_one()

        sessions_today: int = (await db.execute(
            select(func.count()).select_from(GameSession)
            .where(GameSession.ended_at.isnot(None))
            .where(GameSession.started_at >= today_start)
        )).scalar_one()

        # Player accuracy + agreement + escalation from completed sessions
        sess_stats = (await db.execute(
            select(
                func.avg(GameSession.accuracy).label("avg_accuracy"),
                func.avg(GameSession.agreement_rate).label("avg_agreement"),
                func.avg(
                    case(
                        (GameSession.total_decisions > 0,
                         cast(GameSession.total_escalated, Float) / GameSession.total_decisions),
                        else_=None,
                    )
                ).label("avg_esc_rate"),
            ).where(GameSession.ended_at.isnot(None))
        )).one()

        avg_accuracy = float(sess_stats.avg_accuracy or 0.0)
        agreement_rate = float(sess_stats.avg_agreement or 0.0)
        escalation_rate = float(sess_stats.avg_esc_rate or 0.0)

        # Override accuracy: decisions where player disagreed with GORK
        override_row = (await db.execute(
            select(
                func.count().label("total"),
                func.sum(case((PlayerDecision.player_correct == True, 1), else_=0)).label("correct"),  # noqa: E712
            ).where(PlayerDecision.agreed_with_agent == False)  # noqa: E712
        )).one()
        override_total = int(override_row.total or 0)
        override_accuracy = float(override_row.correct or 0) / override_total if override_total > 0 else 0.0

        # Avg latency
        avg_latency: float = float((await db.execute(
            select(func.avg(PlayerDecision.latency_ms))
        )).scalar_one() or 0.0)

        # Sessions by day — last 14 days
        day_rows = (await db.execute(
            select(
                func.date(GameSession.started_at).label("day"),
                func.count().label("n"),
            )
            .where(GameSession.ended_at.isnot(None))
            .group_by(func.date(GameSession.started_at))
            .order_by(func.date(GameSession.started_at).desc())
            .limit(14)
        )).all()
        sessions_by_day = [
            {"date": str(r.day), "count": r.n}
            for r in reversed(day_rows)
        ]

        # Accuracy by harm category
        cat_rows = (await db.execute(
            select(
                DocumentLibrary.harm_category,
                func.avg(case((PlayerDecision.player_correct == True, 1.0), else_=0.0)).label("acc"),  # noqa: E712
                func.count().label("n"),
            )
            .select_from(PlayerDecision)
            .join(DocumentLibrary, DocumentLibrary.id == PlayerDecision.document_id)
            .where(PlayerDecision.player_verdict != "ESCALATE")
            .group_by(DocumentLibrary.harm_category)
            .having(func.count() >= 5)
            .order_by(DocumentLibrary.harm_category)
        )).all()
        accuracy_by_category = {
            r.harm_category: round(float(r.acc), 4)
            for r in cat_rows
        }

    return AnalyticsSummary(
        total_sessions=total_sessions,
        sessions_today=sessions_today,
        avg_accuracy=round(avg_accuracy, 4),
        agreement_rate=round(agreement_rate, 4),
        override_accuracy=round(override_accuracy, 4),
        escalation_rate=round(escalation_rate, 4),
        avg_latency_ms=round(avg_latency, 1),
        sessions_by_day=sessions_by_day,
        accuracy_by_category=accuracy_by_category,
    )


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(request: Request) -> AnalyticsSummary:
    return await _compute_summary(request)


@router.get("/stream")
async def stream_analytics(request: Request) -> StreamingResponse:
    q: asyncio.Queue[str] = asyncio.Queue()
    request.app.state.sse_queues.append(q)
    logger.info("SSE client connected; total=%d", len(request.app.state.sse_queues))

    async def generator() -> AsyncGenerator[str, None]:
        try:
            summary = await _compute_summary(request)
            yield f"data: {summary.model_dump_json()}\n\n"
            while True:
                await q.get()
                summary = await _compute_summary(request)
                yield f"data: {summary.model_dump_json()}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            try:
                request.app.state.sse_queues.remove(q)
            except ValueError:
                pass
            logger.info("SSE client disconnected; total=%d", len(request.app.state.sse_queues))

    return StreamingResponse(generator(), media_type="text/event-stream")
