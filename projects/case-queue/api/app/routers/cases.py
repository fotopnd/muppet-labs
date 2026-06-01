from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Case, CaseCategory, CaseStatus, Severity
from app.schemas import CaseCreate, CaseDetail, CaseListItem, Page

router = APIRouter(tags=["cases"])


@router.get("/cases", response_model=Page[CaseListItem])
async def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    category: CaseCategory | None = None,
    severity: Severity | None = None,
    status: CaseStatus | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: AsyncSession = Depends(get_db),
) -> Page[CaseListItem]:
    filters = _build_filters(category, severity, status, date_from, date_to)

    total_result = await db.execute(select(func.count()).select_from(Case).where(*filters))
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    items_result = await db.execute(
        select(Case)
        .where(*filters)
        .order_by(Case.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = list(items_result.scalars().all())

    return Page(items=items, total=total, page=page, page_size=page_size)


@router.post("/cases", response_model=CaseDetail, status_code=201)
async def create_case(
    body: CaseCreate,
    db: AsyncSession = Depends(get_db),
) -> CaseDetail:
    now = datetime.now(UTC)
    case = Case(
        id=str(uuid.uuid4()),
        content=body.content,
        category=body.category,
        severity=body.severity,
        status=CaseStatus.pending,
        source=body.source,
        meta=body.meta,
        created_at=now,
        updated_at=now,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case, attribute_names=["decisions"])
    return case  # type: ignore[return-value]


@router.get("/cases/{case_id}", response_model=CaseDetail)
async def get_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
) -> CaseDetail:
    result = await db.execute(
        select(Case).where(Case.id == case_id).options(selectinload(Case.decisions))
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case {case_id!r} not found")
    return case  # type: ignore[return-value]


def _build_filters(
    category: CaseCategory | None,
    severity: Severity | None,
    status: CaseStatus | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> list:
    filters = []
    if category is not None:
        filters.append(Case.category == category)
    if severity is not None:
        filters.append(Case.severity == severity)
    if status is not None:
        filters.append(Case.status == status)
    if date_from is not None:
        filters.append(Case.created_at >= date_from)
    if date_to is not None:
        filters.append(Case.created_at <= date_to)
    return filters
