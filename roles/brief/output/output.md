# Brief — red-team-platform v5: Safeguards Portfolio Hardening

**Role:** brief
**Sequence:** add-feature
**Date:** 2026-06-15

## Project Name
`red-team-platform-v5`

## Description
Close five portfolio gaps in red-team-platform that are directly called out in two Anthropic Safeguards SWE job descriptions: stateful case review with persisted decisions, an audit log, SSE streaming replay on the Analytics tab, an auto-triage layer that pre-classifies obvious-safe runs, and GitHub Actions CI/CD — all within the existing FastAPI + React/TypeScript + PostgreSQL stack.

## Language(s)
Python (backend) + TypeScript (frontend) — mixed, full-stack

## Context: Two Target Job Descriptions

**JD 1 — Software Engineer, Safeguards Foundations (Internal Tooling)** (5191433008)
Explicit requirements:
- "Design, build, and maintain the internal review and enforcement tooling used by Safeguards analysts"
- "Developing reusable APIs, data storage, and backend services for review workflows"
- "Building security controls including granular permissions, audit trails, data-access controls"
- "Instrumenting tools to surface metrics on queue health and decision quality"
- Case-management or workflow system design background (preferred)

**JD 2 — Software Engineer, Safeguards Infrastructure** (5074908008)
Explicit requirements:
- "Infrastructure for data storage and management, metric and evaluation systems, and tooling for review processes"
- "Reducing the amount of human intervention and oversight required"
- "Building robust and reliable multi-layered defenses for real-time improvement of safety mechanisms that work at scale"

Both roles are Anthropic London, £255k–£325k. Portfolio must speak to both simultaneously.

## Features in Scope

### Feature 1 — Stateful Case Review
Upgrade the existing read-only SampleReview page into a genuine case management workflow.
- Rename tab/page to "Case Review"
- Add `case_reviews` table: `id UUID PK, run_id UUID FK runs.id, decision ENUM(approve|flag|escalate), reason TEXT nullable, reviewed_at TIMESTAMPTZ DEFAULT now(), reviewer TEXT`
- Backend: `POST /runs/{run_id}/review` — upsert a decision for a run (insert or update if exists)
- Backend: `GET /runs/{run_id}/review` — fetch existing decision for a run (404 if none)
- Frontend: On each run card/row, show a decision form (Approve / Flag / Escalate buttons + optional reason textarea)
- Frontend: Show current decision state inline (colour-coded badge: green=approve, amber=flag, red=escalate)
- Frontend: Prevent duplicate submissions — if decision exists, show it with an "Edit" option to resubmit
- Reviewer identity: hardcoded string "analyst-1" (v1 simplification; noted explicitly in UI)

### Feature 2 — Audit Log
Persist every review decision to a queryable audit trail.
- Add `audit_log` table: `id UUID PK, run_id UUID, action TEXT, decision TEXT, reason TEXT, reviewer TEXT, created_at TIMESTAMPTZ DEFAULT now()`
- Every `POST /runs/{run_id}/review` appends a row to `audit_log` (append-only; latest decision wins for display, full history in log)
- Backend: `GET /audit-log?decision=&reviewer=&limit=50&offset=0` — paginated, filterable
- Frontend: New "Audit Log" tab — table of all decisions with timestamp, reviewer, run excerpt, decision badge, reason
- Frontend: Filter dropdowns for decision type (all/approve/flag/escalate) and reviewer

### Feature 3 — SSE Streaming Replay (Analytics Tab)
Add a live-feed panel to the Analytics tab demonstrating the real-time architectural pattern.
- Backend: `GET /runs/stream?speed=normal` — SSE endpoint; reads all runs from DB ordered by `created_at ASC`; emits one `data:` event per run (JSON: run_id, strategy, harm_category, model_name, classifier_score, jailbreak_success); configurable delay: fast=0ms, normal=50ms, slow=200ms; ends with `event: done\ndata: {}\n\n`
- Frontend: "Live Feed" collapsible section on Analytics tab; scrolling table of last 50 incoming events; Play/Pause button; speed selector (Fast/Normal/Slow); run counter ("2,341 / 11,688"); colour-coded rows by jailbreak_success (red=jailbreak, green=safe)
- Clearly labelled "Replay" in UI; provenance note: "Replaying 11,688 runs collected June 2026"
- SSE uses `text/event-stream`; frontend uses browser `EventSource` API
- FastAPI pattern: `StreamingResponse` with `media_type="text/event-stream"` and async generator

### Feature 4 — Auto-Triage Layer
Pre-sort runs into risk tiers to demonstrate automation reducing manual review load.
- Triage tiers (computed at query time in Python, not stored):
  - `auto_safe`: `classifier_score < 0.15` — clearly below harm threshold; no human review needed
  - `review`: `0.15 ≤ classifier_score < 0.75` — borderline; requires human judgement
  - `auto_flag`: `classifier_score ≥ 0.75` — high-confidence harm signal; auto-flagged, human confirms
- Backend: Add `triage_tier: str` field to existing Run response schema; computed in the `/runs` list and `/runs/{id}` endpoints
- Frontend (Case Review page): Triage filter toggle (All / Needs Review / Auto-Safe / Auto-Flagged)
- Frontend: Tier summary counts at top of Case Review page: "142 need review · 8,944 auto-safe · 2,602 auto-flagged"
- Frontend: Explainer note: "Auto-triage reduces manual queue ~87% — only 0.15–0.75 score range requires human review"
- Backend: `GET /runs/triage-summary` — returns counts per tier (fast aggregate query)

### Feature 5 — GitHub Actions CI/CD
Add CI that runs on every push and PR to main.
- `.github/workflows/ci.yml` — single file, two parallel jobs:
  - `backend`: ubuntu-latest → Python 3.12 → uv → `uv sync` → `uv run ruff check .` → `uv run ruff format --check` → `uv run python -m pytest tests/ -x -q`; working-directory: `projects/red-team-platform`
  - `frontend`: ubuntu-latest → Node 22 → pnpm → `pnpm install` → `pnpm exec tsc --noEmit` → `pnpm vitest run`; working-directory: `projects/red-team-platform/web`
- Note: backend tests require Postgres; use `services: postgres:` in the backend job with `POSTGRES_PASSWORD: redteam`, `POSTGRES_USER: redteam`, `POSTGRES_DB: redteam` on port 5432; override `DATABASE_URL` env var
- Hetzner deploy prep: create `projects/red-team-platform/docker-compose.prod.yml` with nginx reverse proxy stubs — but do NOT implement actual deploy (external account setup required)

## Success Criteria

1. `POST /runs/{run_id}/review` persists a decision; `GET /runs/{run_id}/review` returns it; `GET /audit-log` shows the entry
2. Case Review tab shows triage tier summary counts; "Needs Review" filter loads only borderline runs; decision form submits and badge updates inline without page reload
3. Audit Log tab renders all decisions with working filter dropdowns
4. `GET /runs/stream` emits SSE events in chronological order; frontend Live Feed shows scrolling rows on Play; Pause stops the stream; speed selector works
5. Auto-triage tier is correct: score 0.05 → auto_safe; score 0.50 → review; score 0.90 → auto_flag
6. `.github/workflows/ci.yml` present; backend and frontend jobs defined; `ruff check` passes on existing code; `tsc --noEmit` passes
7. No regressions — all existing tests continue to pass

## Constraints

- **Schema: create_all convention** — new tables (`case_reviews`, `audit_log`) added as ORM models; `Base.metadata.create_all()` on lifespan creates them automatically; no Alembic
- **DB:** `postgresql://redteam:redteam@localhost:5433/redteam`
- **Backend start:** `uv run uvicorn "red_team_platform.api.main:create_app" --factory --host 0.0.0.0 --port 8003`
- **Frontend dev:** `pnpm dev` from `projects/red-team-platform/web/`, port 5173
- **No new Python deps** — SSE via `fastapi.responses.StreamingResponse`; async generator pattern
- **No new frontend deps** — `EventSource` is browser-native; no SSE client library needed
- **asyncpg NULL rule:** Use ORM `.where()` chain for nullable filters; never `text()` with nullable params
- **staleTime for decisions:** 5_000ms (mutable, can change); not Infinity
- **Reviewer identity:** hardcoded "analyst-1"; note as v1 in UI and BUILDOUT.md

## Out of Scope

- Real authentication or role-based permissions
- Llama Guard baseline (separate project)
- Portfolio landing site (separate project)
- Alembic migrations
- WebSockets
- Actual Hetzner deployment (prepare prod compose only)
- Multi-reviewer identity

## Existing Stack Reference

- **Backend routers dir:** `src/red_team_platform/api/routers/` (attacks, bias, clusters, coverage, regression, runs, sessions, strategy)
- **ORM models:** check `src/red_team_platform/api/` for models file; bias models in `bias/models.py`
- **Schemas:** `src/red_team_platform/api/schemas.py`
- **DB engine/session factory:** `src/red_team_platform/db.py` (likely)
- **Factory pattern:** `create_app()` in `src/red_team_platform/api/main.py`
- **Frontend pages:** `web/src/pages/` — SampleReview.tsx to be renamed/replaced by CaseReview.tsx
- **App tabs:** currently defined in `web/src/App.tsx`
- **Model colours:** blue=gemma2:9b, orange=qwen2.5:7b, violet=llama3.1:8b
- **Category keys:** snake_case (post Wave-1 reclassification)

## Assumptions

- `case_reviews` and `audit_log` tables do not yet exist; will be created on next backend restart
- `jailbreak_success` and `classifier_score` are already on `runs` table
- SampleReview page is replaced in-place (same route) by Case Review; route key may change from /sample-review to /case-review
- CI workflow targets pushes and PRs to `main`
- The SSE endpoint does not require auth (consistent with rest of platform)

## Handoff

**Next role:** planner

Planner reads this file and resolves:
1. Exact ORM file locations — where do `CaseReview` and `AuditLogEntry` models go?
2. Router allocation — new `review.py` + `audit.py` routers, or append to `runs.py`?
3. SampleReview rename strategy — new file `CaseReview.tsx` replacing old, or in-place rename?
4. App.tsx tab count after additions — currently 6 tabs; adding Audit Log = 7 tabs; confirm layout
5. SSE generator pattern for async SQLAlchemy — confirm `async def event_generator()` with `AsyncSession` works inside `StreamingResponse`
6. CI Postgres service — confirm `services: postgres:` syntax and health check pattern for GitHub Actions
