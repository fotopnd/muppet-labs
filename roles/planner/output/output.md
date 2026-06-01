# Planner — case-queue

**Role:** planner
**Sequence:** `new-project-full` (step 2 of 6)
**Date:** 2026-06-01
**Reads:** `roles/brief/output/output.md`, `resources/vibecoding-style.md`, `resources/python-conventions.md`, `resources/typescript-conventions.md` (created this session), `skills/setup-uv-project.md`, `skills/setup-ts-pnpm.md` (created this session)

---

## Project

**Name:** `case-queue`
**Location:** `projects/case-queue/`
**Description:** Fullstack case management tool for trust & safety analysts — React/TypeScript frontend with case queue, content review, decision logging, and role-based approve/reject/escalate workflow; backed by a Python FastAPI service and PostgreSQL.

---

## Requirements

### API Requirements

| # | Requirement |
|---|-------------|
| R1 | `GET /cases` returns a paginated JSON response with fields: `items` (list), `total`, `page`, `page_size`. Accepts query params: `page` (default 1), `page_size` (default 50, max 100), `category`, `severity`, `status`, `date_from`, `date_to`. |
| R2 | `GET /cases/{id}` returns a single case with all fields including full `content`, `metadata`, and the list of decisions made on that case. Returns 404 if not found. |
| R3 | `POST /cases/{id}/decisions` accepts body `{action, notes}` and headers `X-Actor-Id`, `X-Actor-Role`. Persists the decision and returns it. Returns 403 if `X-Actor-Role=reviewer` and `action=escalate`. Returns 422 if `notes` is empty or missing. |
| R4 | `GET /audit-log` returns a paginated decision log across all cases. Accepts: `page`, `page_size`, `case_id`, `actor_id`, `action`, `date_from`, `date_to`. |
| R5 | All error responses return JSON `{"detail": "<message>"}` with an appropriate HTTP status code. |
| R6 | CORS is configured to allow requests from `http://localhost:5173`. |
| R7 | Database schema is managed via Alembic migrations. Running `alembic upgrade head` twice is idempotent. |
| R8 | `python scripts/seed.py` generates ≥ 500 synthetic cases covering all six Jigsaw categories (`toxic`, `severe_toxic`, `obscene`, `threat`, `insult`, `identity_hate`) and three severity levels (`low`, `medium`, `high`). Running it twice does not create duplicate cases (seed uses deterministic IDs or checks for existing records). |
| R9 | `uv run pytest tests/ -v` passes with no failures. |
| R10 | `uv run ruff check app/ tests/` and `uv run ruff format --check app/ tests/` both exit 0. |

### Frontend Requirements

| # | Requirement |
|---|-------------|
| R11 | The case queue page (`/`) renders a paginated table with columns: ID (first 8 chars), category, severity, status, created date. Table shows 50 rows per page with previous/next controls. |
| R12 | The case queue page has filter controls for category, severity, and status. Changing a filter resets to page 1 and refetches. |
| R13 | The case detail page (`/cases/:id`) renders: full content text, metadata (source, created date, category, severity), a list of prior decisions, and a decision form. |
| R14 | The decision form has an action selector (approve / reject / escalate) and a required notes textarea. The escalate option is visually disabled and non-submittable when `VITE_ACTOR_ROLE=reviewer`. |
| R15 | Submitting the decision form calls `POST /cases/:id/decisions`, shows a loading state during the request, shows a success message on completion, and returns the user to the case queue. |
| R16 | The audit log page (`/audit`) renders a paginated table: timestamp, case ID (linked), actor ID, action, notes (truncated to 80 chars). |
| R17 | API errors (non-2xx responses) display a visible error message to the user — never a blank or frozen screen. |
| R18 | `pnpm build` compiles without TypeScript errors. |
| R19 | `pnpm test` passes with no failures. |

---

## Technology Stack

### Backend

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | Workspace standard |
| Package manager | `uv` | Workspace standard |
| Formatter / linter | `ruff` | Workspace standard |
| Web framework | FastAPI | Async-native, Pydantic v2 integration, auto-generates OpenAPI docs |
| ORM | SQLAlchemy 2.0 (async) | Async `AsyncSession` + `asyncpg` driver; type-safe query building |
| Migrations | Alembic | Standard SQLAlchemy companion; env.py wired for async |
| ASGI server | `uvicorn` | Standard FastAPI runner |
| Data models | Pydantic v2 | Request/response schemas; FastAPI integrates natively |
| Database | PostgreSQL 16 (via Docker Compose) | Matches SWE role JD requirement; `asyncpg` driver |
| Testing | `pytest` + `pytest-asyncio` + `httpx` | `httpx.AsyncClient` for async FastAPI test client |
| Config | `python-dotenv` | Loads `.env` for local dev |

### Frontend

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | TypeScript 5.x (strict) | Workspace standard; SWE role hard requirement |
| Package manager | `pnpm` | Workspace standard |
| Build tool | Vite | Fast HMR, minimal config, standard for React/TS |
| UI framework | React 18 | SWE role hard requirement |
| Routing | React Router v6 | Standard; file-based routing not needed at this scale |
| Server state | TanStack Query v5 | Handles caching, loading/error states; demonstrates modern React patterns |
| Styling | Tailwind CSS v3 + shadcn/ui | Tailwind for utility classes; shadcn/ui for production-quality components owned in-tree |
| Linting / formatting | ESLint (flat config) + Prettier | Workspace standard |
| Testing | Vitest + Testing Library | Workspace standard per `typescript-conventions.md` |

---

## File and Module Structure

```
projects/case-queue/
├── docker-compose.yml              # postgres:16 service on port 5432
├── .env.example                    # DATABASE_URL, VITE_API_URL, VITE_ACTOR_ID, VITE_ACTOR_ROLE
├── README.md
│
├── api/                            # Python FastAPI backend
│   ├── pyproject.toml
│   ├── ruff.toml
│   ├── alembic.ini
│   ├── .env                        # gitignored; copy from .env.example
│   ├── app/                        # importable package
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app, lifespan (DB init), CORS config
│   │   ├── database.py             # async engine, AsyncSession factory, get_db dependency
│   │   ├── models.py               # SQLAlchemy ORM table definitions
│   │   ├── schemas.py              # Pydantic request/response schemas
│   │   ├── deps.py                 # FastAPI dependencies: get_db, get_actor
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── cases.py            # GET /cases, GET /cases/{id}
│   │       ├── decisions.py        # POST /cases/{id}/decisions
│   │       └── audit.py            # GET /audit-log
│   ├── alembic/
│   │   ├── env.py                  # async Alembic env wired to app.database
│   │   └── versions/               # migration scripts
│   ├── scripts/
│   │   └── seed.py                 # generates 500+ synthetic cases; idempotent
│   └── tests/
│       ├── conftest.py             # async test client, test DB session
│       ├── test_cases.py           # R1, R2 — list + detail endpoints
│       ├── test_decisions.py       # R3 — decision creation, role enforcement, validation
│       └── test_audit.py           # R4 — audit log pagination and filters
│
└── web/                            # TypeScript React frontend
    ├── package.json
    ├── pnpm-lock.yaml
    ├── tsconfig.json
    ├── tsconfig.app.json           # strict config per typescript-conventions.md
    ├── vite.config.ts              # path alias, vitest config
    ├── eslint.config.ts
    ├── .prettierrc
    ├── index.html
    └── src/
        ├── main.tsx                # React entry, QueryClientProvider, RouterProvider
        ├── App.tsx                 # route definitions
        ├── api/
        │   ├── client.ts           # base fetch wrapper (injects X-Actor headers, handles errors)
        │   ├── cases.ts            # typed query functions for /cases endpoints
        │   └── audit.ts            # typed query functions for /audit-log
        ├── types/
        │   └── index.ts            # shared domain types: Case, Decision, AuditEntry, ActorRole
        ├── components/
        │   ├── StatusBadge.tsx     # coloured badge for case status
        │   ├── SeverityBadge.tsx   # coloured badge for severity
        │   ├── Pagination.tsx      # prev/next/page controls
        │   └── ErrorMessage.tsx    # standard error display
        ├── pages/
        │   ├── CaseQueue.tsx       # R11, R12 — list + filters
        │   ├── CaseDetail.tsx      # R13, R14, R15 — detail + decision form
        │   └── AuditLog.tsx        # R16 — audit table
        └── test/
            ├── setup.ts            # testing-library jest-dom setup
            ├── CaseQueue.test.tsx
            ├── CaseDetail.test.tsx
            └── AuditLog.test.tsx
```

---

## Brief Assumption Confirmations

| # | Assumption | Resolution |
|---|------------|------------|
| 1 | React + Vite | Confirmed |
| 2 | FastAPI + SQLAlchemy async | Confirmed |
| 3 | Alembic for migrations | Confirmed |
| 4 | Postgres via Docker Compose | Confirmed |
| 5 | Global audit log in v1 | Confirmed in scope — R16, lower build priority than queue and detail |
| 6 | Actor via headers | Confirmed — `X-Actor-Id` + `X-Actor-Role` headers; extracted in `deps.py` |
| 7 | Jigsaw category mapping | Confirmed |
| 8 | Project layout `api/` + `web/` | Confirmed |
| 9 | `typescript-conventions.md` missing | Resolved — created this session |

---

## Open Questions for Architect

1. **Async Alembic env.py:** Standard Alembic `env.py` is synchronous; async SQLAlchemy requires a specific async runner pattern (`run_async_main`). Architect should specify the exact `env.py` structure to avoid a known setup pitfall.
   *Proposed answer:* Use `asyncio.run(run_migrations_online())` with `async_engine_from_config` — the pattern from SQLAlchemy 2.0 async Alembic docs.

2. **Test database isolation:** API tests need a clean database state per test. Options: rollback after each test (transaction savepoints), or a separate test DB spun up per session.
   *Proposed answer:* Use a separate test database (e.g. `case_queue_test`) defined in `conftest.py`; truncate tables between tests. Avoids savepoint complexity with async SQLAlchemy.

3. **Seed idempotency strategy:** Running `seed.py` twice must not duplicate cases. Options: check-before-insert per record, or truncate-then-insert.
   *Proposed answer:* Truncate-then-insert. The seed data is synthetic and deterministic — no value in preserving partial seed state. Add a `--confirm` flag to prevent accidental truncation.

4. **TanStack Query actor header injection:** The `X-Actor-Id` and `X-Actor-Role` headers need to be injected into every API request. Options: set globally on the fetch client, or pass as query context.
   *Proposed answer:* Set in the base `client.ts` fetch wrapper reading from `import.meta.env.VITE_ACTOR_ID` and `VITE_ACTOR_ROLE`. Single place, no per-call noise.

5. **shadcn/ui initialisation:** shadcn/ui requires `npx shadcn@latest init` which writes config and component files. Architect should specify which components to install (Table, Badge, Button, Select, Textarea, Form) so the implementer does not install the full library.
   *Proposed answer:* Install exactly: `table`, `badge`, `button`, `select`, `textarea`, `form`, `toast`. Architect confirms list.

---

## Handoff

**Next role:** architect
**What the architect does with this:**
- Define the SQLAlchemy ORM models (`models.py`) with all column types and relationships.
- Define all Pydantic schemas (`schemas.py`) — request bodies, response shapes, pagination wrapper.
- Specify the FastAPI dependency injection chain (`deps.py`) for `get_db` and `get_actor`.
- Resolve all five open questions above with concrete answers.
- Specify the TypeScript domain types (`types/index.ts`) to match the API response schemas.
- Confirm the shadcn/ui component list (OQ5).

**Flags for architect:**
- OQ1 (async Alembic) and OQ2 (test DB isolation) are the highest-risk items — both have known async SQLAlchemy gotchas. Resolve these with explicit code patterns, not just decisions.
- OQ5 (shadcn/ui init) must be resolved before the implementer runs the setup commands.
