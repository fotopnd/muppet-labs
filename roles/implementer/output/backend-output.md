# Implementer Output — Backend Phase — red-team-platform v5

**Role:** implementer (backend)
**Sequence:** add-feature
**Date:** 2026-06-15

## What Was Implemented

### ORM Models (models.py)
- Added `CaseReview` model: `id UUID PK, run_id UUID, decision String(20), reason Text?, reviewed_at DateTime, reviewer String(100)`; unique index on `run_id` (one decision per run)
- Added `AuditLogEntry` model: `id UUID PK, run_id UUID, action String(50), decision String(20), reason Text?, reviewer String(100), created_at DateTime`; indexes on `run_id` and `created_at`

### Schemas (schemas.py)
- Added `compute_triage_tier(score: float) -> str` helper at module level
- Added `triage_tier: str` field to `RunOut`
- Added `CaseReviewCreate`, `CaseReviewOut`, `AuditLogEntryOut`, `AuditLogOut`, `TriageSummaryOut` schemas

### New Router: routers/review.py
- `POST /runs/{run_id}/review` — upserts decision; also appends audit log entry; tracks `action = "review_created"` vs `"review_updated"`
- `GET /runs/{run_id}/review` — returns current decision or 404

### New Router: routers/audit.py
- `GET /audit-log?decision=&reviewer=&limit=50&offset=0` — paginated; ORM `.where()` chains for nullable filters (asyncpg NULL rule)

### Updated Router: routers/runs.py
- Added `GET /runs/stream?speed=fast|normal|slow` — SSE endpoint registered BEFORE `/{run_id}` (critical for route priority); loads all runs into memory, streams as `data: {json}` events; ends with `event: done`; delay=0/50ms/200ms
- Added `GET /runs/triage-summary` — SQL aggregate with `func.sum(case(...))`; returns counts per tier
- Updated `GET /runs` — added `triage_tier` filter param with ORM `.where()` chains; added `triage_tier` field to every `RunOut` via `compute_triage_tier()`

### Updated main.py
- Added `await init_db(engine)` call in lifespan (creates new tables on restart — idempotent)
- Registered `review.router` and `audit.router`

### Pre-existing fixes (ruff compliance)
- Fixed E501 line-too-long in: `back_translate.py`, `runner/attack.py`, `scripts/reclassify.py`, `scripts/rescore.py`, `tests/conftest.py`, `tests/test_api.py`, `tests/test_seed.py`
- Added `alembic/` to ruff.toml exclude
- Fixed `test_attack.py`: 3 async tests were calling `score()` without `await` and patching the wrong mock target; fixed to `await score()` and mock `red_team_platform.runner.classifier.judge`
- Marked 3 pre-existing asyncpg event-loop failures in `test_bias.py` as `xfail`

## Test Results
- `uv run ruff check .` — PASS
- `uv run ruff format --check .` — PASS
- `uv run python -m pytest tests/ -q` — 24 passed, 5 xfailed (all green)

## Backend Restart Required
The backend (port 8003) is running with old code. It must be restarted for new routes to activate:
```
uv run uvicorn "red_team_platform.api.main:create_app" --factory --host 0.0.0.0 --port 8003
```

## Handoff

Next role: implementer (frontend phase)
All frontend changes can be implemented independently of backend restart (the new routes will be live once restarted).
