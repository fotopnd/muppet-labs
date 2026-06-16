from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import case, func, select, text

from year_zero.api.schemas import AnalyticsSummary, UpliftRow
from year_zero.models import DocumentLibrary, GameSession, PlayerDecision

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


async def _compute_summary(request: Request) -> AnalyticsSummary:
    """Recomputes the full analytics summary from the DB."""
    async with request.app.state.session_factory() as db:
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        # Total and today's sessions
        total_q = await db.execute(select(func.count()).select_from(GameSession))
        total_sessions: int = total_q.scalar_one()

        today_q = await db.execute(
            select(func.count())
            .select_from(GameSession)
            .where(GameSession.started_at >= today_start)
        )
        sessions_today: int = today_q.scalar_one()

        # FP/FN rates (from player_decisions)
        # FP (false negative in safety terms): player CLEARed a harmful doc
        # FN (false positive): player REDACTed a benign doc
        rate_q = await db.execute(
            select(
                func.count().label("total"),
                func.sum(
                    case(
                        (
                            (PlayerDecision.player_verdict == "CLEAR")
                            & (PlayerDecision.player_correct == False),  # noqa: E712
                            1,
                        ),
                        else_=0,
                    )
                ).label("fp_count"),
                func.sum(
                    case(
                        (
                            (PlayerDecision.player_verdict == "REDACT")
                            & (PlayerDecision.player_correct == False),  # noqa: E712
                            1,
                        ),
                        else_=0,
                    )
                ).label("fn_count"),
                func.avg(PlayerDecision.latency_ms).label("avg_latency"),
            ).select_from(PlayerDecision)
        )
        row = rate_q.one()
        total_decisions = row.total or 0
        fp_count = int(row.fp_count or 0)
        fn_count = int(row.fn_count or 0)
        avg_latency = float(row.avg_latency or 0.0)
        global_fp_rate = fp_count / total_decisions if total_decisions > 0 else 0.0
        global_fn_rate = fn_count / total_decisions if total_decisions > 0 else 0.0

        # Phase survival rates
        phase_q = await db.execute(
            select(GameSession.phase_reached, func.count().label("cnt"))
            .where(GameSession.phase_reached.isnot(None))
            .group_by(GameSession.phase_reached)
        )
        phase_rows = phase_q.all()
        total_finished = sum(r.cnt for r in phase_rows) or 1
        phase_counts = {r.phase_reached: r.cnt for r in phase_rows}
        phase_survival = {
            "phase_1": 1.0,
            "phase_2": sum(v for k, v in phase_counts.items() if k >= 2) / total_finished,
            "phase_3": sum(v for k, v in phase_counts.items() if k >= 3) / total_finished,
        }

        # System drift error rate — last 30 completed sessions grouped by date
        drift_q = await db.execute(
            select(
                func.date(GameSession.ended_at).label("date"),
                func.avg(
                    case((GameSession.accuracy.isnot(None), 1 - GameSession.accuracy), else_=None)
                ).label("error_rate"),
            )
            .where(GameSession.ended_at.isnot(None))
            .group_by(func.date(GameSession.ended_at))
            .order_by(func.date(GameSession.ended_at).desc())
            .limit(30)
        )
        drift_rows = drift_q.all()
        system_drift_error_rate = [
            {"date": str(r.date), "error_rate": round(float(r.error_rate or 0.0), 4)}
            for r in reversed(drift_rows)
        ]

        # Escalation rate — overall and by harm category
        esc_total_q = await db.execute(
            select(
                func.count().label("total"),
                func.sum(
                    case((PlayerDecision.player_verdict == "ESCALATE", 1), else_=0)
                ).label("escalated"),
            ).select_from(PlayerDecision)
        )
        esc_row = esc_total_q.one()
        esc_total = int(esc_row.total or 0)
        esc_count = int(esc_row.escalated or 0)
        escalation_rate = esc_count / esc_total if esc_total > 0 else 0.0

        esc_cat_q = await db.execute(
            select(
                DocumentLibrary.harm_category,
                func.count().label("total"),
                func.sum(
                    case((PlayerDecision.player_verdict == "ESCALATE", 1), else_=0)
                ).label("escalated"),
            )
            .select_from(PlayerDecision)
            .join(DocumentLibrary, DocumentLibrary.id == PlayerDecision.document_id)
            .group_by(DocumentLibrary.harm_category)
        )
        esc_cat_rows = esc_cat_q.all()
        escalation_rate_by_category = {
            r.harm_category: round(int(r.escalated or 0) / int(r.total), 4)
            for r in esc_cat_rows
            if int(r.total) > 0
        }

    return AnalyticsSummary(
        total_sessions=total_sessions,
        sessions_today=sessions_today,
        global_fp_rate=round(global_fp_rate, 4),
        global_fn_rate=round(global_fn_rate, 4),
        avg_latency_ms=round(avg_latency, 1),
        phase_survival=phase_survival,
        system_drift_error_rate=system_drift_error_rate,
        escalation_rate=round(escalation_rate, 4),
        escalation_rate_by_category=escalation_rate_by_category,
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
            # Send initial snapshot on connect
            summary = await _compute_summary(request)
            yield f"data: {summary.model_dump_json()}\n\n"
            while True:
                await q.get()  # blocks until "refresh" sentinel arrives
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


@router.get("/uplift", response_model=list[UpliftRow])
async def get_uplift(request: Request) -> list[UpliftRow]:
    async with request.app.state.session_factory() as db:
        result = await db.execute(
            text("""
                SELECT
                    pd.document_id,
                    dl.strategy,
                    dl.harm_category,
                    dl.generation_model,
                    dl.is_harmful,
                    SUM(CASE WHEN pd.agent_condition = 'none' THEN 1 ELSE 0 END)
                        AS no_agent_decisions,
                    AVG(CASE WHEN pd.agent_condition = 'none' AND pd.player_correct
                        THEN 1.0 ELSE 0.0 END)
                        AS no_agent_accuracy,
                    SUM(CASE WHEN pd.agent_condition != 'none' THEN 1 ELSE 0 END)
                        AS agent_decisions,
                    AVG(CASE WHEN pd.agent_condition != 'none' AND pd.player_correct
                        THEN 1.0 ELSE 0.0 END)
                        AS agent_accuracy
                FROM player_decisions pd
                JOIN document_library dl ON dl.id = pd.document_id
                GROUP BY pd.document_id, dl.strategy, dl.harm_category,
                         dl.generation_model, dl.is_harmful
                HAVING
                    SUM(CASE WHEN pd.agent_condition = 'none' THEN 1 ELSE 0 END) >= 5
                    AND SUM(CASE WHEN pd.agent_condition != 'none' THEN 1 ELSE 0 END) >= 5
                ORDER BY pd.document_id
            """)
        )
        rows = result.all()

    return [
        UpliftRow(
            document_id=r.document_id,
            strategy=r.strategy,
            harm_category=r.harm_category,
            generation_model=r.generation_model,
            is_harmful=r.is_harmful,
            no_agent_decisions=int(r.no_agent_decisions),
            no_agent_accuracy=float(r.no_agent_accuracy or 0.0),
            agent_decisions=int(r.agent_decisions),
            agent_accuracy=float(r.agent_accuracy or 0.0),
            document_uplift=float((r.agent_accuracy or 0.0) - (r.no_agent_accuracy or 0.0)),
        )
        for r in rows
    ]
