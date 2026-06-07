from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from error_hide_seek.api.deps import get_db
from error_hide_seek.api.schemas import PaperOut, PapersPageOut
from error_hide_seek.models import Paper

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("", response_model=PapersPageOut)
async def list_papers(
    q: Annotated[str | None, Query()] = None,
    offset: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> PapersPageOut:
    stmt = select(Paper)
    if q:
        stmt = stmt.where(Paper.title.ilike(f"%{q}%"))

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = (await db.scalars(stmt.offset(offset).limit(limit))).all()
    return PapersPageOut(
        items=[PaperOut.model_validate(p) for p in items],
        total=total or 0,
        offset=offset,
        limit=limit,
    )


@router.get("/{paper_id}", response_model=PaperOut)
async def get_paper(paper_id: int, db: AsyncSession = Depends(get_db)) -> PaperOut:
    paper = await db.get(Paper, paper_id)
    if paper is None:
        raise HTTPException(404, "Paper not found")
    return PaperOut.model_validate(paper)
