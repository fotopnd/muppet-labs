# Implementer 6a Output — error-hide-seek Backend

**Role:** implementer (backend phase)
**Sequence:** `new-project-full` (step 6a)
**Date:** 2026-06-07

---

## Status: Complete

All backend implementation tasks are done. Tests pass. Ruff is clean.

---

## Files Written

### Configuration
- `pyproject.toml` — full project metadata, scripts, build-system, pytest config, dev deps
- `ruff.toml` — Python 3.12 target, line-length 100, isort
- `docker-compose.yml` — Postgres 16, port 5436, health check
- `.env.example` — all required environment variables documented
- `alembic.ini` — Alembic config pointing to `sync_database_url`
- `alembic/env.py` — Alembic env with `SYNC_DATABASE_URL` override support
- `alembic/script.py.mako` — migration template
- `alembic/versions/001_initial_schema.py` — full 7-table migration with all indexes

### Package Source
- `error_hide_seek/__init__.py`
- `error_hide_seek/config.py` — `Settings` with `extra="ignore"`, module-level singleton
- `error_hide_seek/models.py` — all 7 ORM models + 3 enums (`ErrorCategory`, `Condition`, `SessionStatus`)
- `error_hide_seek/db.py` — async engine, sessionmaker, `init_db()`, `get_db()` dep
- `error_hide_seek/corpus/__init__.py`
- `error_hide_seek/corpus/arxiv.py` — `fetch_abstracts()` with Atom XML parsing, 0.4s rate limit
- `error_hide_seek/corpus/fetch.py` — `fetch-corpus` CLI entry point
- `error_hide_seek/agents/__init__.py`
- `error_hide_seek/agents/prompts.py` — `build_red_team_prompt()`, `build_blue_team_prompt()`, all 5 category instructions
- `error_hide_seek/agents/red_team.py` — `plant_error()` with retry logic, `original_text` substring validation
- `error_hide_seek/agents/blue_team.py` — `annotate()` with retry + silent fallback on double failure
- `error_hide_seek/agents/plant.py` — `plant-errors` CLI with `--experiment-id` + optional `--category`
- `error_hide_seek/scoring/__init__.py`
- `error_hide_seek/scoring/scorer.py` — `is_true_positive()`, `score_detections()`, `compute_experiment_results()`, `score_cli()`
- `error_hide_seek/api/__init__.py`
- `error_hide_seek/api/schemas.py` — all request/response Pydantic models; `DetectionIn.min_length=15`; `SessionOut.paper_title` included
- `error_hide_seek/api/deps.py` — `get_db()` FastAPI dependency
- `error_hide_seek/api/main.py` — FastAPI app with lifespan, CORS, all routers mounted
- `error_hide_seek/api/routers/__init__.py`
- `error_hide_seek/api/routers/health.py` — `GET /health`
- `error_hide_seek/api/routers/papers.py` — `GET /papers`, `GET /papers/{id}`
- `error_hide_seek/api/routers/experiments.py` — `POST /experiments`, `GET /experiments`, `GET /experiments/{id}`
- `error_hide_seek/api/routers/sessions.py` — `POST /sessions` (blue team on-demand, auto-score for `agent_only`), `GET /sessions/{id}`
- `error_hide_seek/api/routers/reviews.py` — `POST /reviews` (score and mark complete)
- `error_hide_seek/api/routers/results.py` — `GET /results/{experiment_id}`

### Tests
- `tests/conftest.py` — NullPool engine, per-test TRUNCATE isolation, `db_session` + `client` fixtures
- `tests/test_scoring.py` — 8 unit tests for `is_true_positive` and `score_detections`
- `tests/test_arxiv.py` — 2 tests for arXiv XML parsing (mocked via `pytest-httpserver`)
- `tests/test_agents.py` — 7 tests for red-team and blue-team agents (mocked Anthropic client)
- `tests/test_api.py` — 9 integration tests covering health, papers, experiments, sessions, reviews, results, 409 double-submit, 422 min-length

### Results
- `results/findings.md` — stub table for experiment results

---

## Key Decisions

| Decision | Resolution |
|----------|-----------|
| Altered abstract storage | `planted_errors.altered_abstract` computed at plant time |
| Agent calls at startup | Never — created per-request inside route handlers |
| `agent_only` session | Synchronous: POST /sessions blocks until Claude annotates + scores |
| Scoring rule | Case-insensitive substring containment in either direction; min 15 chars |
| Condition assignment | Deterministic positional split: first ⌊N/3⌋ → unaided, next ⌊N/3⌋ → agent_only, remainder → human_agent |
| `paper_title` in `SessionOut` | Added via join in sessions router (not a separate fetch) |
| Test isolation | Per-test `TRUNCATE ... RESTART IDENTITY CASCADE`; NullPool avoids cross-loop connection issues |
| `greenlet` dep | Added explicitly — SQLAlchemy async requires it; not installed by default on macOS |

---

## Test Results

```
26 passed in 1.11s
```

```
ruff check . → All checks passed!
ruff format --check . → All files already formatted
```

---

## Handoff

**Next role:** implementer 6b (frontend)

**Frontend implementer reads:**
- `roles/architect/output/output.md` — frontend types, hook specs, component specs
- `roles/design-brief/output/output.md` — done criteria, visual register
- `roles/frontend-architect/output/output.md` — token layer, page layouts, component hierarchy, constraints
- This file (for `paper_title` field in `SessionOut`, `DetectionIn.min_length=15`, port 5174)

**Ports:**
- API: `http://localhost:8004`
- Frontend: `http://localhost:5174`

**Start API:** `uv run api` (starts uvicorn with reload)

**Quick smoke test after DB is up:**
```bash
docker compose up -d db
uv run fetch-corpus  # populates papers
POST /experiments with paper_ids from /papers
uv run plant-errors --experiment-id 1
POST /sessions to start reviewing
```
