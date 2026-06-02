# Architect — case-queue

**Role:** architect
**Sequence:** `new-project-full` (step 3 of 6)
**Date:** 2026-06-01
**Reads:** `roles/planner/output/output.md`, `resources/python-conventions.md`, `resources/typescript-conventions.md`

---

## Open Questions Resolved

| # | Question | Resolution |
|---|----------|------------|
| OQ1 | Async Alembic `env.py` pattern | Use `asyncio.run(run_migrations_online())` with `async_engine_from_config` + `NullPool`. Exact pattern in Implementation Notes. |
| OQ2 | Test database isolation | Separate `case_queue_test` database. Truncate all tables between tests via a session-scoped autouse fixture. Connection string from `TEST_DATABASE_URL` env var. |
| OQ3 | Seed idempotency | `TRUNCATE cases, decisions RESTART IDENTITY CASCADE` before insert. `--confirm` flag required to prevent accidental run. Seed data generated synthetically — no Kaggle auth required. |
| OQ4 | Header injection for TanStack Query | Base `apiFetch` wrapper in `api/client.ts` reads `VITE_ACTOR_ID` and `VITE_ACTOR_ROLE` from `import.meta.env` and injects them into every request. |
| OQ5 | shadcn/ui components to install | `table`, `badge`, `button`, `select`, `textarea`, `form`, `toast`. Run `npx shadcn@latest init` then `npx shadcn@latest add <component>` for each. |

---

## System Overview

Three processes communicate at runtime: a Vite dev server serving the React SPA, a FastAPI ASGI process serving the REST API, and a PostgreSQL instance. The SPA makes fetch requests to FastAPI; FastAPI queries PostgreSQL via SQLAlchemy async sessions. All three start with a single `docker compose up` (Postgres) followed by two terminal commands. There is no message queue, no background worker, and no websocket — all operations are synchronous request/response.

Within the API, requests flow through FastAPI dependency injection: `get_db` yields an `AsyncSession` scoped to the request lifetime; `get_actor` parses `X-Actor-Id` / `X-Actor-Role` headers into an `Actor` dataclass. Routers call neither the database nor the session factory directly — they receive both through injected dependencies.

When a decision is created, the handler updates `cases.status` and `cases.updated_at` in the same transaction before committing, keeping case status in sync with the latest decision without a separate background process.

---

## Data Models

### Backend ORM (`app/models.py`)

```python
from __future__ import annotations
import enum
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CaseCategory(str, enum.Enum):
    toxic         = "toxic"
    severe_toxic  = "severe_toxic"
    obscene       = "obscene"
    threat        = "threat"
    insult        = "insult"
    identity_hate = "identity_hate"


class Severity(str, enum.Enum):
    low    = "low"
    medium = "medium"
    high   = "high"


class CaseStatus(str, enum.Enum):
    pending   = "pending"
    approved  = "approved"
    rejected  = "rejected"
    escalated = "escalated"


class Action(str, enum.Enum):
    approve  = "approve"
    reject   = "reject"
    escalate = "escalate"


class ActorRole(str, enum.Enum):
    reviewer        = "reviewer"
    senior_reviewer = "senior_reviewer"


class Case(Base):
    __tablename__ = "cases"
    __table_args__ = (
        Index("ix_cases_status",     "status"),
        Index("ix_cases_category",   "category"),
        Index("ix_cases_severity",   "severity"),
        Index("ix_cases_created_at", "created_at"),
    )

    id:         Mapped[str]          = mapped_column(String,            primary_key=True)
    content:    Mapped[str]          = mapped_column(Text,              nullable=False)
    category:   Mapped[CaseCategory] = mapped_column(SAEnum(CaseCategory), nullable=False)
    severity:   Mapped[Severity]     = mapped_column(SAEnum(Severity),  nullable=False)
    status:     Mapped[CaseStatus]   = mapped_column(SAEnum(CaseStatus), nullable=False, default=CaseStatus.pending)
    source:     Mapped[str]          = mapped_column(String,            nullable=False)
    meta:       Mapped[dict]         = mapped_column(JSONB,             nullable=False, default=dict)
    created_at: Mapped[datetime]     = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime]     = mapped_column(DateTime(timezone=True), nullable=False)

    decisions: Mapped[list[Decision]] = relationship(
        "Decision", back_populates="case", order_by="Decision.created_at"
    )


class Decision(Base):
    __tablename__ = "decisions"
    __table_args__ = (
        Index("ix_decisions_case_id",    "case_id"),
        Index("ix_decisions_actor_id",   "actor_id"),
        Index("ix_decisions_created_at", "created_at"),
    )

    id:         Mapped[str]       = mapped_column(String,             primary_key=True)
    case_id:    Mapped[str]       = mapped_column(String,             ForeignKey("cases.id"), nullable=False)
    actor_id:   Mapped[str]       = mapped_column(String,             nullable=False)
    actor_role: Mapped[ActorRole] = mapped_column(SAEnum(ActorRole),  nullable=False)
    action:     Mapped[Action]    = mapped_column(SAEnum(Action),     nullable=False)
    notes:      Mapped[str]       = mapped_column(Text,               nullable=False)
    created_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), nullable=False)

    case: Mapped[Case] = relationship("Case", back_populates="decisions")
```

### Backend Pydantic Schemas (`app/schemas.py`)

```python
from __future__ import annotations
from datetime import datetime
from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field
from app.models import CaseCategory, Severity, CaseStatus, Action, ActorRole

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items:     list[T]
    total:     int
    page:      int
    page_size: int


class DecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:         str
    actor_id:   str
    actor_role: ActorRole
    action:     Action
    notes:      str
    created_at: datetime


class CaseListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:         str
    category:   CaseCategory
    severity:   Severity
    status:     CaseStatus
    created_at: datetime


class CaseDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:         str
    content:    str
    category:   CaseCategory
    severity:   Severity
    status:     CaseStatus
    source:     str
    meta:       dict
    created_at: datetime
    updated_at: datetime
    decisions:  list[DecisionRead]


class DecisionCreate(BaseModel):
    action: Action
    notes:  str = Field(min_length=1)


class AuditEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:         str
    case_id:    str
    actor_id:   str
    actor_role: ActorRole
    action:     Action
    notes:      str
    created_at: datetime
```

### TypeScript Domain Types (`src/types/index.ts`)

```typescript
export type CaseCategory =
  | 'toxic' | 'severe_toxic' | 'obscene'
  | 'threat' | 'insult' | 'identity_hate'

export type Severity    = 'low' | 'medium' | 'high'
export type CaseStatus  = 'pending' | 'approved' | 'rejected' | 'escalated'
export type Action      = 'approve' | 'reject' | 'escalate'
export type ActorRole   = 'reviewer' | 'senior_reviewer'

export interface Decision {
  id:         string
  actor_id:   string
  actor_role: ActorRole
  action:     Action
  notes:      string
  created_at: string   // ISO 8601
}

export interface CaseListItem {
  id:         string
  category:   CaseCategory
  severity:   Severity
  status:     CaseStatus
  created_at: string
}

export interface CaseDetail {
  id:         string
  content:    string
  category:   CaseCategory
  severity:   Severity
  status:     CaseStatus
  source:     string
  meta:       Record<string, unknown>
  created_at: string
  updated_at: string
  decisions:  Decision[]
}

export interface AuditEntry {
  id:         string
  case_id:    string
  actor_id:   string
  actor_role: ActorRole
  action:     Action
  notes:      string
  created_at: string
}

export interface Page<T> {
  items:     T[]
  total:     number
  page:      number
  page_size: number
}

export interface DecisionCreate {
  action: Action
  notes:  string
}

export interface CaseFilters {
  page?:      number
  page_size?: number
  category?:  CaseCategory
  severity?:  Severity
  status?:    CaseStatus
  date_from?: string
  date_to?:   string
}

export interface AuditFilters {
  page?:      number
  page_size?: number
  case_id?:   string
  actor_id?:  string
  action?:    Action
  date_from?: string
  date_to?:   string
}
```

---

## Module Interfaces

### `app/database.py`

```python
from __future__ import annotations
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
)
from app.models import Base

def make_engine(database_url: str) -> AsyncEngine:
    """Create async engine. Called once at startup."""

async_session_factory: async_sessionmaker[AsyncSession]   # module-level, set in init_db()

async def init_db(database_url: str) -> None:
    """Create engine, session factory, and run CREATE TABLE IF NOT EXISTS for all models.
    Called inside FastAPI lifespan. Sets module-level async_session_factory.
    """

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency. Yields one AsyncSession per request; commits on clean exit,
    rolls back on exception, always closes."""
```

### `app/deps.py`

```python
from __future__ import annotations
from dataclasses import dataclass
from fastapi import Header, HTTPException
from app.models import ActorRole

@dataclass(frozen=True)
class Actor:
    id:   str
    role: ActorRole

async def get_actor(
    x_actor_id:   str = Header(),
    x_actor_role: str = Header(),
) -> Actor:
    """Parse X-Actor-Id and X-Actor-Role headers into Actor.
    Raises HTTP 400 if x_actor_role is not a valid ActorRole value.
    Raises HTTP 422 automatically if headers are absent (FastAPI Header default).
    """
```

### `app/routers/cases.py`

```python
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.schemas import Page, CaseListItem, CaseDetail
from app.models import CaseCategory, Severity, CaseStatus
from app.database import get_db

router = APIRouter(tags=["cases"])

@router.get("/cases", response_model=Page[CaseListItem])
async def list_cases(
    page:      int                  = Query(1, ge=1),
    page_size: int                  = Query(50, ge=1, le=100),
    category:  CaseCategory | None  = None,
    severity:  Severity | None      = None,
    status:    CaseStatus | None    = None,
    date_from: datetime | None      = None,
    date_to:   datetime | None      = None,
    db:        AsyncSession         = Depends(get_db),
) -> Page[CaseListItem]:
    """SELECT with dynamic WHERE clauses. ORDER BY created_at DESC.
    COUNT(*) in a subquery for total. OFFSET/LIMIT for pagination.
    """

@router.get("/cases/{case_id}", response_model=CaseDetail)
async def get_case(
    case_id: str,
    db:      AsyncSession = Depends(get_db),
) -> CaseDetail:
    """SELECT with selectinload(Case.decisions). Returns 404 if not found."""
```

### `app/routers/decisions.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import DecisionCreate, DecisionRead
from app.models import Action, ActorRole
from app.database import get_db
from app.deps import get_actor, Actor

router = APIRouter(tags=["decisions"])

@router.post("/cases/{case_id}/decisions", response_model=DecisionRead, status_code=201)
async def create_decision(
    case_id: str,
    body:    DecisionCreate,
    actor:   Actor          = Depends(get_actor),
    db:      AsyncSession   = Depends(get_db),
) -> DecisionRead:
    """1. Fetch case by id — 404 if missing.
    2. Enforce: if actor.role == reviewer and body.action == escalate → 403.
    3. INSERT Decision with uuid4() id and datetime.now(UTC).
    4. UPDATE Case.status to match body.action mapping; UPDATE Case.updated_at.
    5. Commit. Return DecisionRead.
    Action → status mapping: approve→approved, reject→rejected, escalate→escalated.
    """
```

### `app/routers/audit.py`

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.schemas import Page, AuditEntry
from app.models import Action
from app.database import get_db

router = APIRouter(tags=["audit"])

@router.get("/audit-log", response_model=Page[AuditEntry])
async def get_audit_log(
    page:      int            = Query(1, ge=1),
    page_size: int            = Query(50, ge=1, le=100),
    case_id:   str | None     = None,
    actor_id:  str | None     = None,
    action:    Action | None  = None,
    date_from: datetime | None = None,
    date_to:   datetime | None = None,
    db:        AsyncSession   = Depends(get_db),
) -> Page[AuditEntry]:
    """SELECT decisions with dynamic WHERE. ORDER BY created_at DESC.
    No join to cases needed — AuditEntry carries case_id as a plain field.
    """
```

### `app/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.config import settings
from app.routers import cases, decisions, audit

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(settings.database_url)
    yield

app = FastAPI(title="case-queue API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router)
app.include_router(decisions.router)
app.include_router(audit.router)
```

### `app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/case_queue"
    model_config = {"env_file": ".env"}

settings = Settings()
```

### `src/api/client.ts`

```typescript
const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Actor-Id':   import.meta.env.VITE_ACTOR_ID   ?? 'dev-user',
      'X-Actor-Role': import.meta.env.VITE_ACTOR_ROLE ?? 'reviewer',
      ...options.headers,
    },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }))
    throw new ApiError(response.status, (body as { detail: string }).detail)
  }
  return response.json() as Promise<T>
}
```

### `src/api/cases.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from './client'
import type { CaseListItem, CaseDetail, DecisionCreate, Decision, Page, CaseFilters } from '@/types'

function toCaseParams(filters: CaseFilters): string {
  // Serialize defined fields only into URLSearchParams
}

export function useCases(filters: CaseFilters) {
  return useQuery({
    queryKey: ['cases', filters],
    queryFn:  () => apiFetch<Page<CaseListItem>>(`/cases?${toCaseParams(filters)}`),
  })
}

export function useCase(id: string) {
  return useQuery({
    queryKey: ['cases', id],
    queryFn:  () => apiFetch<CaseDetail>(`/cases/${id}`),
  })
}

export function useCreateDecision(caseId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: DecisionCreate) =>
      apiFetch<Decision>(`/cases/${caseId}/decisions`, {
        method: 'POST',
        body:   JSON.stringify(body),
      }),
    onSuccess: () => {
      // Invalidate both list and the specific case detail
      queryClient.invalidateQueries({ queryKey: ['cases'] })
      queryClient.invalidateQueries({ queryKey: ['audit-log'] })
    },
  })
}
```

### `src/api/audit.ts`

```typescript
import { useQuery } from '@tanstack/react-query'
import { apiFetch } from './client'
import type { AuditEntry, AuditFilters, Page } from '@/types'

export function useAuditLog(filters: AuditFilters) {
  return useQuery({
    queryKey: ['audit-log', filters],
    queryFn:  () => apiFetch<Page<AuditEntry>>(`/audit-log?${toAuditParams(filters)}`),
  })
}
```

---

## Dependencies Map

```
app/main.py
  → app/database.py    (init_db, get_db)
  → app/config.py      (settings)
  → app/routers/*      (include_router)

app/routers/cases.py
  → app/database.py    (get_db)
  → app/models.py      (ORM classes, enums)
  → app/schemas.py     (Page, CaseListItem, CaseDetail)

app/routers/decisions.py
  → app/database.py    (get_db)
  → app/deps.py        (get_actor, Actor)
  → app/models.py      (Action, Case, Decision enums)
  → app/schemas.py     (DecisionCreate, DecisionRead)

app/routers/audit.py
  → app/database.py    (get_db)
  → app/models.py      (Action enum)
  → app/schemas.py     (Page, AuditEntry)

app/deps.py
  → app/models.py      (ActorRole)

app/schemas.py
  → app/models.py      (enums only — no ORM imports in schemas)

app/database.py
  → app/models.py      (Base.metadata)

scripts/seed.py
  → app/database.py    (engine)
  → app/models.py      (Case, CaseCategory, Severity, CaseStatus)
  → app/config.py      (settings)
```

No circular dependencies. `app/models.py` is the leaf node — it imports nothing from `app/`.

Frontend dependency flow:
```
pages/* → api/cases.ts, api/audit.ts → api/client.ts
pages/* → components/*
api/*   → types/index.ts
```

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Error handling (API) | Routers raise `HTTPException` with explicit status codes. FastAPI serialises to `{"detail": "..."}`. No global exception handler needed — FastAPI's default covers unhandled exceptions as HTTP 500. |
| Error handling (frontend) | `apiFetch` throws `ApiError` on non-2xx. TanStack Query exposes `error` state; pages render `<ErrorMessage>` component when `isError` is true. |
| Configuration (API) | `pydantic-settings` `BaseSettings` reads `.env`. Single `settings` singleton imported where needed. |
| Configuration (frontend) | `import.meta.env.VITE_*` for all runtime config. Values set in `.env` file at project root. |
| Logging | `logging.getLogger(__name__)` per module. FastAPI default logs to stdout at `INFO`. No structured logging needed for a portfolio project. |
| DB session lifetime | One `AsyncSession` per request, injected via `get_db` dependency. Commit on clean exit, rollback on exception. Never share sessions across requests. |
| UUID generation | `uuid.uuid4()` for Decision IDs. Case IDs are generated by the seed script using the same strategy. |
| Datetime handling | All datetimes stored as timezone-aware UTC. `datetime.now(UTC)` throughout. Serialised as ISO 8601 in JSON responses. |
| Testing | API: `pytest-asyncio` with `httpx.AsyncClient` against a test DB. Frontend: Vitest + Testing Library + `msw` for API mocking. |

---

## Implementation Notes for Implementer

1. **Async Alembic `env.py` — exact pattern:**
   ```python
   import asyncio
   from sqlalchemy.pool import NullPool
   from sqlalchemy.ext.asyncio import async_engine_from_config
   from alembic import context
   from app.models import Base

   target_metadata = Base.metadata

   async def run_migrations_online() -> None:
       cfg = context.config.get_section(context.config.config_ini_section, {})
       connectable = async_engine_from_config(cfg, prefix="sqlalchemy.", poolclass=NullPool)
       async with connectable.connect() as connection:
           await connection.run_sync(
               lambda conn: context.configure(conn, target_metadata=target_metadata)
           )
           async with connection.begin():
               await connection.run_sync(lambda _: context.run_migrations())
       await connectable.dispose()

   if context.is_offline_mode():
       run_migrations_offline()   # standard sync implementation
   else:
       asyncio.run(run_migrations_online())
   ```
   Set `sqlalchemy.url` in `alembic.ini` using an env var: `%(DATABASE_URL)s` — Alembic interpolates from environment.

2. **`pydantic-settings` for config:** Add `pydantic-settings` as a dependency (`uv add pydantic-settings`). It is not bundled with pydantic v2.

3. **`selectinload` for decisions:** In `get_case`, use `selectinload(Case.decisions)` on the SQLAlchemy select to avoid the N+1 problem. Do not use `joinedload` — it produces duplicate rows with one-to-many.

4. **Pagination query pattern:** For `list_cases` and `get_audit_log`, run two queries: one `SELECT COUNT(*)` with filters applied, one `SELECT ... LIMIT ... OFFSET ...` with the same filters. SQLAlchemy 2.0 style:
   ```python
   count_stmt = select(func.count()).select_from(Case).where(*filters)
   total = (await db.execute(count_stmt)).scalar_one()
   items_stmt = select(Case).where(*filters).order_by(Case.created_at.desc()).offset(offset).limit(page_size)
   items = (await db.execute(items_stmt)).scalars().all()
   ```

5. **Status update in `create_decision`:** After inserting the Decision, execute:
   ```python
   status_map = {Action.approve: CaseStatus.approved, Action.reject: CaseStatus.rejected, Action.escalate: CaseStatus.escalated}
   await db.execute(update(Case).where(Case.id == case_id).values(status=status_map[body.action], updated_at=datetime.now(UTC)))
   ```
   Both INSERT and UPDATE run before the single `await db.commit()`.

6. **Seed script synthetic data:** Do not download from Kaggle. Generate programmatically: use `random.choice` to pick categories and severities, use a small set of template sentences per category (5–10 per category × confidence multiplier for severity). Generate at least 500 rows, evenly distributed across 6 categories × 3 severities = 18 buckets (~28 per bucket). Set `source="seed:jigsaw-synthetic"`.

7. **shadcn/ui initialisation order:**
   ```bash
   pnpm dlx shadcn@latest init          # configures tailwind, sets up components/ui/
   pnpm dlx shadcn@latest add table badge button select textarea form toast
   ```
   Run from `web/` directory. shadcn writes component files into `src/components/ui/` — do not edit these manually.

8. **`VITE_ACTOR_ROLE` controls escalate visibility:** In `CaseDetail.tsx`, read `import.meta.env.VITE_ACTOR_ROLE` directly to disable the escalate option in the Select component. Do not derive this from API response data.

9. **Test database setup:** Add to `api/tests/conftest.py`:
   ```python
   TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/case_queue_test")

   @pytest.fixture(scope="session", autouse=True)
   async def setup_test_db():
       engine = create_async_engine(TEST_DATABASE_URL)
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
       yield
       await engine.dispose()

   @pytest.fixture(autouse=True)
   async def truncate_tables(db_session):
       yield
       await db_session.execute(text("TRUNCATE cases, decisions RESTART IDENTITY CASCADE"))
       await db_session.commit()
   ```

10. **`pytest-asyncio` mode:** Add to `pyproject.toml`:
    ```toml
    [tool.pytest.ini_options]
    asyncio_mode = "auto"
    ```
    This avoids `@pytest.mark.asyncio` on every test function.

11. **`.env.example` contents:**
    ```
    # API
    DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/case_queue
    TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/case_queue_test

    # Frontend
    VITE_API_URL=http://localhost:8000
    VITE_ACTOR_ID=dev-user
    VITE_ACTOR_ROLE=senior_reviewer
    ```

---

## Handoff

**Next role:** implementer
**What the implementer does:**
1. Set up Docker Compose with Postgres.
2. Initialise `api/` with `uv` (following `skills/setup-uv-project.md`).
3. Initialise `web/` with `pnpm` + Vite (following `skills/setup-ts-pnpm.md`).
4. Implement in dependency order: `models.py` → `database.py` → `config.py` → `deps.py` → `schemas.py` → routers → `main.py` → `seed.py` → API tests.
5. Implement frontend in order: `types/index.ts` → `api/client.ts` → `api/cases.ts` + `api/audit.ts` → shared components → pages → frontend tests.
6. Run Alembic init (`alembic init alembic`) and write `env.py` using the async pattern from Implementation Note 1.
7. Verify end-to-end: `docker compose up -d`, `uv run uvicorn app.main:app --reload`, `pnpm dev`, open `http://localhost:5173`.

**Flags for implementer:**
- Implementation Note 1 (async Alembic `env.py`) is the highest-risk setup step. Do it before writing any migration scripts.
- Implementation Note 3 (`selectinload` vs `joinedload`) matters for correctness on the case detail endpoint.
- shadcn/ui must be initialised before writing any page components that import from `@/components/ui`.
