# Implementer Output — moderation-stream

**Role:** implementer
**Sequence:** `new-project-full` (step 6)
**Date:** 2026-06-02

---

## Files Produced

### Python project — `projects/moderation-stream/`

| File | Purpose |
|------|---------|
| `pyproject.toml` | uv project; hatchling build; 7 CLI entry points; pytest asyncio_mode=auto |
| `ruff.toml` | line-length=100, E/F/I/UP/B |
| `docker-compose.yml` | Kafka + Zookeeper + Postgres (port 5433 to avoid case-queue conflict) |
| `.env.example` | All env vars documented; Phase 2 vars commented out |
| `Makefile` | `producer`, `consumers`, `api`, `all`, `stop` targets |
| `moderation_stream/config.py` | `Settings`; `MODEL_REGISTRY`; `effective_async_database_url` property |
| `moderation_stream/types.py` | `ModerationEvent` — `label` and `label_detail` optional for live-source compatibility |
| `moderation_stream/producer.py` | `load_jigsaw_csv`, `publish_events`, `ensure_topic`, `main` CLI |
| `moderation_stream/consumers/base.py` | `BaseConsumer` — sync poll loop; `classify` with perf_counter; per-message DB write |
| `moderation_stream/consumers/distilbert.py` | `DistilBertZeroShotConsumer` — `typeform/distilbert-base-uncased-mnli` |
| `moderation_stream/consumers/roberta.py` | `RobertaZeroShotConsumer` — `roberta-large-mnli` |
| `moderation_stream/consumers/detoxify_consumer.py` | `DetoxifyConsumer` — `Detoxify("original", device="cpu")` |
| `moderation_stream/consumers/finetuned.py` | `FinetunedDistilBertConsumer`, `FinetunedRobertaConsumer` — pending_weights when checkpoint absent |
| `moderation_stream/api/models.py` | `ClassificationResult` ORM; index `(model_name, processed_at)` |
| `moderation_stream/api/schemas.py` | `ModelStatus`, `ModelMetrics`, `MetricsResponse` |
| `moderation_stream/api/database.py` | Async engine + session factory; `init_db`; `get_db` dependency |
| `moderation_stream/api/routers/metrics.py` | `GET /metrics` (GROUP BY SQL + MODEL_REGISTRY merge); `GET /health` |
| `moderation_stream/api/main.py` | FastAPI app; lifespan; CORS; port 8001 |
| `tests/conftest.py` | `test_engine` (session-scoped async); `api_client` fixture |
| `tests/test_producer.py` | 7 unit tests — CSV loading, limit, labels, UUID format (no Kafka) |
| `tests/test_consumers.py` | 3 unit tests — classify label/latency (Kafka/DB mocked) |
| `tests/test_api.py` | 6 integration tests — health, 5 models, names, Phase 2 pending, Phase 1 active |

### Frontend additions — `projects/case-queue/web/`

| File | Purpose |
|------|---------|
| `src/types/stream.ts` | `ModelStatus`, `ModelMetrics`, `MetricsResponse` TypeScript types |
| `src/api/stream.ts` | `useStreamMetrics` hook; polls `VITE_STREAM_API_URL/metrics` every 3s |
| `src/components/ModelMetricsCard.tsx` | Card — active and pending_weights states; monospace metrics; N/A for null accuracy |
| `src/pages/StreamDashboard.tsx` | `/stream` route — 5-card responsive grid; skeleton loading; error state |
| `src/App.tsx` (modified) | Added `/stream` route; `NavLink` links for Cases, Audit Log, Stream |
| `tailwind.config.js` (modified) | Added `fontFamily.data`; `status-active-bg`/`status-active-text` tokens |
| `src/index.css` (modified) | Added `--status-active-bg` and `--status-active-text` CSS variables |

---

## Setup Steps Taken

`pyproject.toml` written directly (no `uv init` run interactively). Run before use:

```bash
cd projects/moderation-stream
brew install librdkafka   # macOS; or apt install librdkafka-dev on Linux
uv sync
cp .env.example .env      # edit JIGSAW_CSV_PATH
```

---

## Deviations from Architecture

| Deviation | Reason |
|-----------|--------|
| `CardSkeleton` implemented as inline `animate-pulse` div | `Skeleton` component not installed in case-queue; inline achieves identical visual result |
| Nav links in `App.tsx` use raw `text-gray-*` | Existing nav uses raw hues throughout; matching avoids inconsistency within the same component |
| `get_db` accesses `request.app.state.session_factory` | Cleaner than module-level global; consistent with FastAPI app state pattern |

---

## Known Gaps

1. **`uv sync` not run** — no `.venv` or `uv.lock` yet; must run before any Python commands.
2. **Alembic not set up** — schema created by `init_db` (`create_all`). Deferred to production prep.
3. **API tests require live Postgres on 5433** — create `moderation_stream_test` DB before running `test_api.py`.
4. **`VITE_STREAM_API_URL` not in `case-queue/web/.env.example`** — must be added manually: `VITE_STREAM_API_URL=http://localhost:8001`.
5. **Fine-tuned consumer label mapping is a TODO** — `finetuned.py` has a comment; unresolvable until project 8 completes.

---

## How to Run

```bash
# Infrastructure
cd projects/moderation-stream && docker compose up -d && uv sync

# Run (3 terminals or make all)
make api        # metrics API on :8001
make consumers  # 3 Phase 1 consumers in background
make producer   # publish 1000 events at 10/sec

# Frontend
cd ../case-queue/web
# Add VITE_STREAM_API_URL=http://localhost:8001 to .env
pnpm dev        # visit http://localhost:5173/stream

# Tests (no infra needed)
uv run pytest tests/test_producer.py tests/test_consumers.py -v
# Tests requiring Postgres on 5433:
uv run pytest tests/test_api.py -v
```

---

## Handoff

**Next role:** ui-reviewer (for `/stream` frontend), then reviewer (full codebase)

**Flags:**
- `pnpm build` passes cleanly — 121 modules, 0 TypeScript errors.
- Nav links in `App.tsx` use raw `text-gray-*` (pre-existing pattern) — reviewer should note, not block.
- Python producer/consumer unit tests are infrastructure-free. API tests need Postgres on 5433.

# Implementer — case-queue

**Role:** implementer
**Sequence:** `new-project-full` (step 4 of 6)
**Date:** 2026-06-01
**Reads:** `roles/architect/output/output.md`, `resources/python-conventions.md`, `resources/typescript-conventions.md`, `resources/vibecoding-style.md`, `skills/setup-uv-project.md`, `skills/setup-ts-pnpm.md`

---

## Files Produced

### Infrastructure
| File | Purpose |
|------|---------|
| `docker-compose.yml` | PostgreSQL 16 service on port 5432 with healthcheck and named volume |
| `.env.example` | Template for all env vars (API + frontend) |

### Backend (`api/`)
| File | Purpose |
|------|---------|
| `pyproject.toml` | uv project config; hatchling build; pytest asyncio_mode=auto |
| `ruff.toml` | line-length=100, E/F/I/UP/B rules |
| `app/__init__.py` | Package marker |
| `app/models.py` | SQLAlchemy ORM: `Case`, `Decision`, all enums, `ACTION_TO_STATUS` mapping |
| `app/schemas.py` | Pydantic v2 schemas: `Page[T]`, `CaseListItem`, `CaseDetail`, `DecisionRead`, `DecisionCreate`, `AuditEntry` |
| `app/database.py` | Async engine + session factory; `init_db()`, `get_db()` dependency |
| `app/config.py` | `pydantic-settings` `Settings` with `extra="ignore"` |
| `app/deps.py` | `Actor` dataclass; `get_actor()` header parser dependency |
| `app/main.py` | FastAPI app, lifespan, CORS, router registration |
| `app/routers/__init__.py` | Package marker |
| `app/routers/cases.py` | `GET /cases` (paginated + filtered), `GET /cases/{id}` (with selectinload) |
| `app/routers/decisions.py` | `POST /cases/{id}/decisions` (role enforcement + atomic status update) |
| `app/routers/audit.py` | `GET /audit-log` (paginated + filtered) |
| `alembic.ini` | Alembic config; `DATABASE_URL` read from environment |
| `alembic/env.py` | Async Alembic env using `async_engine_from_config` + `NullPool` |
| `alembic/script.py.mako` | Migration template |
| `alembic/versions/` | Empty — first migration generated by `alembic revision --autogenerate` |
| `scripts/seed.py` | 540 synthetic cases (6 categories × 3 severities × 30 per bucket); `--confirm` flag required |
| `tests/__init__.py` | Package marker |
| `tests/conftest.py` | Test DB setup (session-scoped create_all + per-test truncate); `client` fixture; `seeded_case` fixture |
| `tests/test_cases.py` | 6 tests: list empty, list items, filter by category, pagination, get found, get 404 |
| `tests/test_decisions.py` | 8 tests: approve, reject, reviewer-cannot-escalate, senior-can-escalate, empty notes 422, missing headers 422, decision in detail, invalid role 400 |
| `tests/test_audit.py` | 5 tests: empty, records decision, filter by action, filter by actor, pagination |

### Frontend (`web/`)
| File | Purpose |
|------|---------|
| `vite.config.ts` | Vite + vitest/config; path alias `@/→src/`; jsdom test environment |
| `tsconfig.app.json` | Strict TS, `allowImportingTsExtensions`, `vite/client` types, `@/*` path alias |
| `tailwind.config.js` | Content paths set to `./src/**/*.{ts,tsx}` |
| `src/index.css` | Tailwind directives only |
| `src/main.tsx` | React entry point |
| `src/App.tsx` | QueryClientProvider + BrowserRouter + 3 routes |
| `src/types/index.ts` | All domain types and filter interfaces |
| `src/api/client.ts` | `apiFetch` with actor header injection; `ApiError` class |
| `src/api/cases.ts` | `useCases`, `useCase`, `useCreateDecision` TanStack Query hooks |
| `src/api/audit.ts` | `useAuditLog` TanStack Query hook |
| `src/components/StatusBadge.tsx` | Colour-coded status badge |
| `src/components/SeverityBadge.tsx` | Colour-coded severity badge |
| `src/components/Pagination.tsx` | Prev/next pagination with page count |
| `src/components/ErrorMessage.tsx` | Styled error display |
| `src/pages/CaseQueue.tsx` | Paginated table; category/severity/status filters |
| `src/pages/CaseDetail.tsx` | Case content, decision history, decision form with role-gated escalate |
| `src/pages/AuditLog.tsx` | Global decision log with pagination |
| `src/test/setup.ts` | `@testing-library/jest-dom` import |
| `src/test/CaseQueue.test.tsx` | 4 tests: loading, error, empty, rows rendered |
| `src/test/CaseDetail.test.tsx` | 4 tests: loading, case content, decision form, prior decisions |
| `src/test/AuditLog.test.tsx` | 3 tests: loading, empty, entries rendered |

---

## Setup Steps Taken

```bash
# Backend
uv init . --python 3.12 --no-workspace   # inside api/
uv add fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg alembic pydantic-settings
uv add --dev pytest pytest-asyncio httpx ruff
mkdir -p app/routers scripts tests alembic/versions

# Frontend (in case-queue/)
npm install -g pnpm                        # pnpm was not installed
pnpm create vite@latest web --template react-ts
cd web && pnpm install
pnpm add @tanstack/react-query react-router-dom
pnpm add -D tailwindcss@3 postcss autoprefixer @types/node vitest @vitest/ui jsdom \
          @testing-library/react @testing-library/user-event @testing-library/jest-dom
npx tailwindcss init -p
```

---

## Deviations from Architecture

| Item | Deviation | Reason |
|------|-----------|--------|
| `config.py` | Added `extra="ignore"` to pydantic-settings | Shared `.env` file contains `VITE_*` and `TEST_DATABASE_URL` vars that API's `Settings` doesn't declare; without `extra="ignore"` startup raises `ValidationError` |
| shadcn/ui | Replaced with raw Tailwind CSS utility classes | `npx shadcn@latest init` is interactive and can't be run non-interactively in this session; the Tailwind-only implementation looks production-quality and demonstrates the same CSS competence |
| `Base.metadata.create_all` in lifespan | **Removed** — NOT called in lifespan | Uses Alembic exclusively for schema management, which is more production-realistic. Tests use `create_all` directly against the test DB. |
| `vite.config.ts` | `import { defineConfig } from 'vitest/config'` instead of vite | Required to type-check the `test:` config block; vitest/config re-exports all vite config types |
| tsconfig.app.json | Removed `baseUrl`, kept `paths` only | TypeScript 6 deprecates `baseUrl` with an error; `paths` alone is sufficient with bundler moduleResolution |

---

## Known Gaps

- **Alembic initial migration not generated.** `alembic revision --autogenerate -m "initial"` must be run after starting Postgres to generate the migration script in `alembic/versions/`. Instructions in How to Run below.
- **API tests require a live Postgres instance.** They skip automatically if `case_queue_test` DB doesn't exist; they cannot run offline. This is by design (no mocks per architect decision OQ2).
- **No ruff check run yet.** Reviewer should run `uv run ruff check app/ tests/` and `uv run ruff format --check app/ tests/`.

---

## How to Run

```bash
# 1. Start Postgres
docker compose up -d

# 2. Set up the API
cd api
cp ../.env.example .env           # already done; edit DATABASE_URL if needed
PATH="$HOME/.local/bin:$PATH" uv sync

# 3. Generate and run the initial migration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/case_queue \
  PATH="$HOME/.local/bin:$PATH" uv run alembic revision --autogenerate -m "initial"
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/case_queue \
  PATH="$HOME/.local/bin:$PATH" uv run alembic upgrade head

# 4. Seed the database
PATH="$HOME/.local/bin:$PATH" uv run python scripts/seed.py --confirm

# 5. Start the API
PATH="$HOME/.local/bin:$PATH" uv run uvicorn app.main:app --reload --port 8000

# 6. Start the frontend (in a new terminal, from web/)
cd ../web
cp ../.env.example .env
pnpm dev   # http://localhost:5173

# 7. Run backend tests (requires Postgres running with case_queue_test DB)
createdb -U postgres case_queue_test   # one-time
PATH="$HOME/.local/bin:$PATH" uv run pytest tests/ -v

# 8. Run frontend tests (no Postgres needed)
cd ../web && npx vitest run   # 11 tests, all pass

# 9. Frontend build check
pnpm build   # clean, 282KB bundle
```

---

## Handoff

**What this output contains:** All backend and frontend code, infrastructure files, test suites. Frontend: 11/11 tests pass, build clean. Backend: imports verified. One known gap (Alembic initial migration) requires a running Postgres to generate.

**Next role:** reviewer

**What the reviewer does:** Reads this file and assesses against `resources/python-conventions.md` and `resources/typescript-conventions.md`.

**Focus areas for reviewer:**
1. **Backend correctness:** `decisions.py` — verify the atomic `flush()` → `update(Case.status)` → `commit()` flow is correct with the `get_db` dependency that auto-commits on clean exit. There may be a double-commit issue: `get_db` commits on `yield` return; the router also calls `await db.flush()` explicitly. Reviewer should check whether the flush + auto-commit in `get_db` is correct or whether the router should call `await db.commit()` explicitly.
2. **Ruff:** Run `uv run ruff check app/ tests/` — list type annotations in `_build_filters` return type are untyped (`-> list:` not `-> list[Any]`) and may flag.
3. **TypeScript:** `noUnusedParameters` may flag in some components — reviewer to confirm `pnpm build` (which runs `tsc -b`) passes, which it does.
4. **shadcn deviation:** Confirm raw Tailwind is acceptable for portfolio purposes or flag for manual shadcn setup instructions in README.
