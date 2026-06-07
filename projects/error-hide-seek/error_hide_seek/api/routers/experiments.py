from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from error_hide_seek.api.deps import get_db
from error_hide_seek.api.schemas import (
    ExperimentCreate,
    ExperimentOut,
    ExperimentPaperOut,
    ExperimentSummaryOut,
)
from error_hide_seek.models import Condition, Experiment, ExperimentPaper, Paper

router = APIRouter(prefix="/experiments", tags=["experiments"])


def _assign_conditions(paper_ids: list[int]) -> list[tuple[int, str]]:
    n = len(paper_ids)
    third = n // 3
    conditions = (
        [Condition.UNAIDED] * third
        + [Condition.AGENT_ONLY] * third
        + [Condition.HUMAN_AGENT] * (n - 2 * third)
    )
    return list(zip(paper_ids, [c.value for c in conditions], strict=False))


@router.post("", response_model=ExperimentOut, status_code=201)
async def create_experiment(
    body: ExperimentCreate, db: AsyncSession = Depends(get_db)
) -> ExperimentOut:
    exp = Experiment(name=body.name, description=body.description)
    db.add(exp)
    await db.flush()

    papers_data: list[ExperimentPaperOut] = []
    for paper_id, condition in _assign_conditions(body.paper_ids):
        paper = await db.get(Paper, paper_id)
        if paper is None:
            await db.rollback()
            raise HTTPException(404, f"Paper {paper_id} not found")
        ep = ExperimentPaper(experiment_id=exp.id, paper_id=paper_id, condition=condition)
        db.add(ep)
        papers_data.append(
            ExperimentPaperOut(
                paper_id=paper_id, title=paper.title, arxiv_id=paper.arxiv_id, condition=condition
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
