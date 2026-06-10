import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from error_hide_seek.api.deps import get_db
from error_hide_seek.api.schemas import (
    ExperimentCreate,
    ExperimentOut,
    ExperimentPaperOut,
    ExperimentSummaryOut,
    SessionListItemOut,
)
from error_hide_seek.models import CATEGORY_CYCLE, Condition, Experiment, ExperimentPaper, Paper, ReviewSession

router = APIRouter(prefix="/experiments", tags=["experiments"])


def _assign_conditions_and_categories(
    paper_ids: list[int],
    experiment_id: int,
) -> list[tuple[int, str, str]]:
    """Return (paper_id, condition, intended_category) with seeded deterministic assignment.

    Shuffles paper order using experiment_id as the RNG seed so the same
    experiment always produces the same assignment (reproducible for reruns).
    Categories are distributed in round-robin order after shuffling.
    """
    rng = random.Random(experiment_id)
    shuffled = list(paper_ids)
    rng.shuffle(shuffled)

    n = len(shuffled)
    third = n // 3
    conditions = (
        [Condition.UNAIDED] * third
        + [Condition.AGENT_ONLY] * third
        + [Condition.HUMAN_AGENT] * (n - 2 * third)
    )

    # Round-robin categories so each condition sees a spread of error types.
    categories = [CATEGORY_CYCLE[i % len(CATEGORY_CYCLE)] for i in range(n)]

    return [
        (pid, str(cond), cat)
        for pid, cond, cat in zip(shuffled, conditions, categories, strict=False)
    ]


@router.post("", response_model=ExperimentOut, status_code=201)
async def create_experiment(
    body: ExperimentCreate, db: AsyncSession = Depends(get_db)
) -> ExperimentOut:
    exp = Experiment(name=body.name, description=body.description)
    db.add(exp)
    await db.flush()

    papers_data: list[ExperimentPaperOut] = []
    for paper_id, condition, intended_category in _assign_conditions_and_categories(
        body.paper_ids, exp.id
    ):
        paper = await db.get(Paper, paper_id)
        if paper is None:
            await db.rollback()
            raise HTTPException(404, f"Paper {paper_id} not found")
        ep = ExperimentPaper(
            experiment_id=exp.id,
            paper_id=paper_id,
            condition=condition,
            intended_category=intended_category,
        )
        db.add(ep)
        papers_data.append(
            ExperimentPaperOut(
                paper_id=paper_id,
                title=paper.title,
                arxiv_id=paper.arxiv_id,
                condition=condition,
                intended_category=intended_category,
            )
        )

    await db.commit()
    return ExperimentOut(
        id=exp.id,
        name=exp.name,
        description=exp.description,
        created_at=exp.created_at,
        papers=papers_data,
    )


@router.get("", response_model=list[ExperimentSummaryOut])
async def list_experiments(db: AsyncSession = Depends(get_db)) -> list[ExperimentSummaryOut]:
    rows = (
        await db.execute(
            select(
                Experiment,
                func.count(ExperimentPaper.id).label("paper_count"),
            )
            .outerjoin(ExperimentPaper, ExperimentPaper.experiment_id == Experiment.id)
            .group_by(Experiment.id)
            .order_by(Experiment.created_at.desc())
        )
    ).all()
    return [
        ExperimentSummaryOut(
            id=exp.id,
            name=exp.name,
            description=exp.description,
            created_at=exp.created_at,
            paper_count=count,
        )
        for exp, count in rows
    ]


@router.get("/{experiment_id}/sessions", response_model=list[SessionListItemOut])
async def list_experiment_sessions(
    experiment_id: int, db: AsyncSession = Depends(get_db)
) -> list[SessionListItemOut]:
    rows = (
        await db.scalars(
            select(ReviewSession)
            .where(ReviewSession.experiment_id == experiment_id)
            .order_by(ReviewSession.condition, ReviewSession.id)
        )
    ).all()
    return [SessionListItemOut(session_id=r.id, condition=r.condition, status=r.status) for r in rows]


@router.get("/{experiment_id}", response_model=ExperimentOut)
async def get_experiment(experiment_id: int, db: AsyncSession = Depends(get_db)) -> ExperimentOut:
    exp = await db.get(Experiment, experiment_id)
    if exp is None:
        raise HTTPException(404, "Experiment not found")

    rows = (
        await db.execute(
            select(ExperimentPaper, Paper)
            .join(Paper, Paper.id == ExperimentPaper.paper_id)
            .where(ExperimentPaper.experiment_id == experiment_id)
        )
    ).all()

    papers = [
        ExperimentPaperOut(
            paper_id=ep.paper_id,
            title=p.title,
            arxiv_id=p.arxiv_id,
            condition=ep.condition,
            intended_category=ep.intended_category,
        )
        for ep, p in rows
    ]
    return ExperimentOut(
        id=exp.id,
        name=exp.name,
        description=exp.description,
        created_at=exp.created_at,
        papers=papers,
    )
