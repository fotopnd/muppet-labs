from datetime import UTC, datetime

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from error_hide_seek.agents.blue_team import annotate
from error_hide_seek.api.deps import get_db
from error_hide_seek.api.schemas import AnnotationOut, AutoScoredResult, SessionCreate, SessionOut
from error_hide_seek.config import settings
from error_hide_seek.models import (
    AgentAnnotation,
    AgentRunStatus,
    Condition,
    ExperimentPaper,
    HumanDetection,
    Paper,
    PlantedError,
    ReviewSession,
)
from error_hide_seek.scoring.scorer import is_true_positive, score_detections

router = APIRouter(prefix="/sessions", tags=["sessions"])


async def _build_session_out(
    session_row: ReviewSession,
    abstract_text: str,
    paper_title: str,
    annotations: list[AnnotationOut],
    scored_result: AutoScoredResult | None,
) -> SessionOut:
    return SessionOut(
        session_id=session_row.id,
        experiment_id=session_row.experiment_id,
        paper_id=session_row.paper_id,
        paper_title=paper_title,
        condition=session_row.condition,
        status=session_row.status,
        abstract_text=abstract_text,
        annotations=annotations,
        scored_result=scored_result,
        agent_run_status=session_row.agent_run_status,
        parse_failures=session_row.parse_failures,
    )


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)) -> SessionOut:
    ep = await db.scalar(
        select(ExperimentPaper).where(
            ExperimentPaper.experiment_id == body.experiment_id,
            ExperimentPaper.paper_id == body.paper_id,
        )
    )
    if ep is None:
        raise HTTPException(404, "Paper not in experiment")

    pe = await db.scalar(
        select(PlantedError).where(
            PlantedError.paper_id == body.paper_id,
            PlantedError.experiment_id == body.experiment_id,
        )
    )
    if pe is None:
        raise HTTPException(422, "Errors not yet planted for this paper")

    paper = await db.get(Paper, body.paper_id)
    paper_title = paper.title if paper else ""

    session_row = ReviewSession(
        experiment_id=body.experiment_id,
        paper_id=body.paper_id,
        condition=ep.condition,
    )
    db.add(session_row)
    await db.flush()

    annotations: list[AnnotationOut] = []
    scored_result: AutoScoredResult | None = None

    if ep.condition == Condition.HUMAN_AGENT:
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        ann_result = await annotate(client, pe.altered_abstract)
        session_row.parse_failures = ann_result.parse_failures
        session_row.agent_run_status = (
            AgentRunStatus.PARSE_FAILED
            if not ann_result.annotations and ann_result.parse_failures > 0
            else AgentRunStatus.SUCCESS
        )

        for ann in ann_result.annotations:
            ann_row = AgentAnnotation(
                review_session_id=session_row.id,
                text_excerpt=ann.text_excerpt,
                confidence=ann.confidence,
                reason=ann.reason,
            )
            db.add(ann_row)
        await db.flush()

        saved = (
            await db.scalars(
                select(AgentAnnotation).where(AgentAnnotation.review_session_id == session_row.id)
            )
        ).all()
        annotations = [
            AnnotationOut(
                id=a.id, text_excerpt=a.text_excerpt, confidence=a.confidence, reason=a.reason
            )
            for a in saved
        ]

    elif ep.condition == Condition.AGENT_ONLY:
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        ann_result = await annotate(client, pe.altered_abstract)
        session_row.parse_failures = ann_result.parse_failures
        session_row.agent_run_status = (
            AgentRunStatus.PARSE_FAILED
            if not ann_result.annotations and ann_result.parse_failures > 0
            else AgentRunStatus.SUCCESS
        )

        # Low-confidence annotations are excluded from auto-scoring to reduce
        # false positives. The threshold is confidence == "low" (string enum from
        # the blue-team prompt), not a numeric comparison.
        trustworthy = [a for a in ann_result.annotations if a.confidence != "low"]
        excerpts = [a.text_excerpt for a in trustworthy]
        planted_detected, fp_count = score_detections(excerpts, pe.original_text)

        for ann in trustworthy:
            db.add(
                HumanDetection(
                    review_session_id=session_row.id,
                    text_excerpt=ann.text_excerpt,
                    is_true_positive=is_true_positive(ann.text_excerpt, pe.original_text),
                )
            )

        session_row.status = "completed"
        session_row.completed_at = datetime.now(UTC)
        tpr = 1.0 if planted_detected else 0.0
        fpr = fp_count / len(excerpts) if excerpts else 0.0
        scored_result = AutoScoredResult(
            true_positives=1 if planted_detected else 0,
            false_positives=fp_count,
            tpr=tpr,
            fpr=fpr,
        )

    else:
        # UNAIDED — no agent involved
        session_row.agent_run_status = AgentRunStatus.SKIPPED
        session_row.parse_failures = 0

    await db.commit()
    return await _build_session_out(
        session_row, pe.altered_abstract, paper_title, annotations, scored_result
    )


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: int, db: AsyncSession = Depends(get_db)) -> SessionOut:
    session_row = await db.get(ReviewSession, session_id)
    if session_row is None:
        raise HTTPException(404, "Session not found")

    pe = await db.scalar(
        select(PlantedError).where(
            PlantedError.paper_id == session_row.paper_id,
            PlantedError.experiment_id == session_row.experiment_id,
        )
    )
    if pe is None:
        raise HTTPException(500, "Planted error missing for session")

    paper = await db.get(Paper, session_row.paper_id)
    paper_title = paper.title if paper else ""

    saved_anns = (
        await db.scalars(
            select(AgentAnnotation).where(AgentAnnotation.review_session_id == session_id)
        )
    ).all()
    annotations = [
        AnnotationOut(
            id=a.id, text_excerpt=a.text_excerpt, confidence=a.confidence, reason=a.reason
        )
        for a in saved_anns
    ]

    return await _build_session_out(
        session_row, pe.altered_abstract, paper_title, annotations, None
    )
