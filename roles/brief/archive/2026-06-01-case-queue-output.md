# Brief Output — case-queue

**Role:** brief
**Sequence:** `new-project-full` (step 1 of 6)
**Date:** 2026-06-01

---

## Project Name

`case-queue`

---

## Description

A fullstack case management tool for trust & safety analysts: a React/TypeScript frontend with a paginated case queue, content review surface, decision logging UI, and approve/reject/escalate workflow — backed by a Python FastAPI service and PostgreSQL.

---

## Language(s)

Mixed:
- **Frontend:** TypeScript (React, strict mode)
- **Backend:** Python (FastAPI)
- **Database:** PostgreSQL
- **Tooling:** pnpm (frontend), uv (backend), Docker Compose (Postgres local)

---

## Success Criteria

The project is done when all of the following are true:

1. **Case queue view** — lists cases with pagination; filterable by category, severity, and date; each row shows case ID, category, severity, status, and created timestamp.
2. **Case detail view** — shows full case payload (content text, source, metadata), plus a review decision form with action selector (approve / reject / escalate) and a required notes field.
3. **Audit log view** — every decision is persisted to PostgreSQL with actor ID, action, notes, and timestamp; viewable per-case and as a global log page.
4. **Role-based action controls** — two hardcoded roles: `reviewer` (can approve/reject) and `senior_reviewer` (can also escalate). Role is set via a request header (`X-Actor-Role`) — no real auth required.
5. **Seed data** — at least 500 synthetic cases seeded from Jigsaw Toxic Comments patterns, covering all categories and severity levels.
6. **Runs locally end-to-end** — `docker compose up` starts Postgres; `uv run uvicorn` starts the API; `pnpm dev` starts the frontend. All three work together without manual config.
7. **README** — clear enough for a hiring manager to clone, run, and understand in under 10 minutes.

---

## Constraints

- **Portfolio-first:** must look and feel production-quality, not like a tutorial project. No toy UI, no placeholder data, no debug traces left in.
- **Freely available dataset only:** synthetic data seeded from Jigsaw Toxic Comments (Kaggle, free) — no Meta data, no proprietary sources.
- **Local-only deployment:** no cloud deployment required; Docker Compose covers all infrastructure.
- **No real authentication:** mock role system via header is sufficient. The point is to demonstrate the permission model, not an auth server.
- **TypeScript strict mode throughout:** demonstrates production-quality TS, which is the core gap to close.

---

## Out of Scope

- Real user authentication / OAuth / JWT
- Cloud deployment or CI/CD pipeline
- Live data ingestion (no streaming, no webhooks from external sources)
- ML model integration (no classifier running in-process — data is pre-labelled from seed)
- Mobile layout / responsive design (desktop-only is fine for a portfolio tool)
- Multi-tenancy or multi-team support
- Email or notification delivery on decisions

---

## Assumptions

> These were inferred from the project_ideas.md description and the SWE role JD. Flag any that the planner should revisit.

1. **React + Vite** for the frontend build (fastest local dev experience; no SSR needed for an internal tool).
2. **FastAPI + SQLAlchemy (async)** for the backend — standard modern Python API stack.
3. **Alembic** for database migrations — standard companion to SQLAlchemy.
4. **Postgres via Docker Compose** for local dev; connection string via `.env`.
5. **Two primary frontend views for v1:** case queue (list) and case detail (single case + decision form). Global audit log is a third view at lower priority — include if time allows.
6. **Actor identity** is a hardcoded string passed as a request header (`X-Actor-Id`) alongside `X-Actor-Role` — no login flow.
7. **Jigsaw Toxic Comments categories** map to case categories: `toxic`, `severe_toxic`, `obscene`, `threat`, `insult`, `identity_hate`. Severity is derived from label confidence scores.
8. **Project lives at** `projects/case-queue/` with two subdirectories: `api/` (Python) and `web/` (TypeScript).
9. **`typescript-conventions.md` does not yet exist.** Planner must create it before the architect role runs. This is a hard dependency.

---

## Handoff

**Next role:** planner
**What the planner does with this:**
- Confirm or revise tech stack assumptions (items 1–4 especially).
- Define the full requirements list, broken into API and frontend.
- Specify the file/module structure for both `api/` and `web/`.
- **Create `resources/typescript-conventions.md`** — this is a blocker for architect and implementer.
- Identify open questions with proposed answers (per routing.md convention).

**Flags for planner:**
- Assumption 9 (missing `typescript-conventions.md`) must be resolved before implementer runs.
- Assumption 5 (global audit log priority) — confirm whether it is in v1 scope or deferred.
