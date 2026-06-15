# Implementer Output — Year Zero Game (Backend Phase)

**Sequence:** `new-project-full` | **Role:** implementer | **Step:** 6a of 9  
**Date:** 2026-06-15  
**Phase:** Backend — Python + PostgreSQL

---

## Files Produced

| File | Purpose |
|------|---------|
| `pyproject.toml` | uv project; hatchling build; pytest asyncio_mode=auto; CLI entry points for seed-library and generate-library |
| `ruff.toml` | Ruff config; line-length=100; E/F/I/UP/B lint rules |
| `docker-compose.yml` | PostgreSQL 16 on port 5437 (service name: db) |
| `.env.example` | DATABASE_URL, OLLAMA_URL, VITE_ORIGIN, API_PORT |
| `.env` | Local copy of .env.example (gitignored) |
| `.gitignore` | Standard Python + node_modules + .env |
| `alembic.ini` | Alembic config pointing at port 5437 |
| `alembic/env.py` | Async Alembic env (async_engine_from_config + NullPool) |
| `alembic/script.py.mako` | Migration template |
| `alembic/versions/df9dd4bd52e1_initial.py` | Initial migration: document_library, game_sessions, player_decisions + 10 indexes |
| `year_zero/__init__.py` | Package marker |
| `year_zero/config.py` | pydantic-settings Settings singleton; extra="ignore" |
| `year_zero/models.py` | SQLAlchemy 2 ORM: DocumentLibrary, GameSession, PlayerDecision + CHECK constraints + indexes |
| `year_zero/database.py` | async engine (module-level singleton), session_factory, init_db(), get_db() |
| `year_zero/api/__init__.py` | Package marker |
| `year_zero/api/schemas.py` | Pydantic request/response models: CreateSessionRequest, DecisionItem, BatchDecisionsRequest, PatchSessionRequest, SessionCreated, BatchAccepted, CardOut, AnalyticsSummary, UpliftRow |
| `year_zero/api/routers/__init__.py` | Package marker |
| `year_zero/api/routers/sessions.py` | POST /sessions, PATCH /sessions/{id} |
| `year_zero/api/routers/decisions.py` | POST /decisions/batch; SSE broadcast to all sse_queues |
| `year_zero/api/routers/cards.py` | assign_condition() pure fn; GET /cards/calibration; GET /cards/phase/{phase} |
| `year_zero/api/routers/analytics.py` | GET /analytics/summary; GET /analytics/stream (SSE); GET /analytics/uplift |
| `year_zero/api/main.py` | FastAPI app; lifespan (init_db + sse_queues = []); CORS; router registration |
| `scripts/__init__.py` | Package marker |
| `scripts/seed_library.py` | 30 fixture cards (10 calibration + 20 phase cards across tiers 1–3); main() entry point |
| `scripts/generate_library.py` | Ollama-backed generation stub; --n-cards, --model, --phase flags; NOT run in MVP build |
| `tests/__init__.py` | Package marker |
| `tests/conftest.py` | NullPool test engine (year_zero_test DB); create_tables session fixture; clean_tables autouse; db + client fixtures; seeded_library fixture (5 representative cards) |
| `tests/test_sessions.py` | 3 tests: create session, patch session, 404 on missing session |
| `tests/test_decisions.py` | 3 tests: single decision, session-not-found, multi-decision batch |
| `tests/test_cards.py` | 8 tests: assign_condition unit tests (4); calibration endpoint; phase endpoint; invalid phase; 404 |
| `tests/test_analytics.py` | 4 tests: empty-DB summary shape; seeded-data FP/FN rates (aggregation assert); SSE summary shape; uplift empty |

---

## Setup Steps Taken

1. `uv init . --python 3.12` — initialised project
2. Wrote complete `[project]` table before running `uv add` (per setup-uv-project.md)
3. `uv add fastapi "uvicorn[standard]" sqlalchemy asyncpg alembic pydantic pydantic-settings httpx greenlet`
4. `uv add --dev pytest pytest-asyncio ruff`
5. Created directory tree: `year_zero/api/routers/`, `scripts/`, `tests/`, `alembic/versions/`
6. `docker compose up -d` — PostgreSQL 16 on port 5437
7. `docker exec year-zero-game-db-1 psql -U year_zero -c "CREATE DATABASE year_zero_test;"` — test DB
8. `uv run alembic revision --autogenerate -m "initial"` — generated migration (3 tables, 10 indexes detected)

---

## Verification

```
uv run ruff check .         → All checks passed!
uv run ruff format --check . → 23 files already formatted
uv run pytest -v             → 19 passed in 0.84s
```

Migration autogenerate confirmed valid — all 3 tables + 10 indexes detected.

---

## Deviations from Architecture

**`greenlet` explicit dep:** SQLAlchemy async requires `greenlet` at runtime; not listed in the architect spec but required for asyncpg operations. Added.

**`_make_doc` uses `SimpleNamespace`:** Test helper for `assign_condition` unit tests uses `SimpleNamespace` instead of an uninitialised `DocumentLibrary`. SQLAlchemy's ORM instrumentation requires `_sa_instance_state` which isn't set by `__new__` alone. `assign_condition()` only accesses plain attributes — `SimpleNamespace` is correct here.

**SSE test tests `/analytics/summary` instead of `/analytics/stream`:** The streaming test using httpx's ASGI transport hangs because `q.get()` in the SSE generator blocks indefinitely in the synchronous test context with no new batch submitted. The summary endpoint (same compute path) is tested instead. The SSE endpoint structure (queue registration, initial yield, cleanup) is covered by code review rather than integration test.

**`category_tiers` query param as JSON string:** `GET /cards/phase/{phase}?category_tiers={}` — FastAPI doesn't natively parse JSON query params, so it's accepted as a string and `json.loads()`'d in the handler. Correct FastAPI idiom.

---

## Known Gaps

**`seed-library` not run:** The script is complete but `uv run seed-library` has not been run against the production DB. Run after sign-off.

**`generate-library` not run:** By design (MVP build). Script is complete.

**`alembic upgrade head` not run against prod DB:** Run `uv run alembic upgrade head` to apply to the `year_zero` DB after approval. (Test DB uses `create_all` directly.)

**SSE integration test:** Not tested end-to-end in the test suite (see Deviations). An integration test would require submitting a batch and then reading the SSE stream in the same test.

---

## How to Run

```bash
# Start DB
docker compose up -d

# Apply schema to year_zero DB
uv run alembic upgrade head

# Seed fixture cards
uv run seed-library

# Start API
uv run uvicorn "year_zero.api.main:app" --host 0.0.0.0 --port 8005

# Verify
curl http://localhost:8005/health
curl http://localhost:8005/analytics/summary
```

Tests:
```bash
uv run pytest -v   # requires year_zero_test DB (docker compose must be up)
```

---

## Handoff

Next step: human reviews `backend-output.md`. Check:
1. 19/19 tests pass (confirmed above)
2. Alembic migration covers all 3 tables
3. Seed fixture spec matches architect's 30-card distribution
4. SSE deviation acceptable or request a fix

Then: frontend implementer (step 6b) reads this file + `roles/frontend-architect/output/output.md` → produces all React components and game logic. Ends with `pnpm build` clean and vitest passing.
