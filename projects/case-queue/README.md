# Case Queue

A fullstack trust and safety case management tool. Content flags arrive through the queue, analysts review each case in detail, and every approve, reject, or escalate decision is logged with actor identity and a timestamp. An optional AI reviewer service (backed by either a local Ollama model or the Claude API) can process the queue automatically, posting decisions back through the same REST endpoints a human analyst would use.

The project covers the full vertical: PostgreSQL schema design, an async FastAPI service, a React and TypeScript frontend with TanStack Query, a Typer CLI for the AI reviewer, and test suites at both layers. It was built to demonstrate the engineering patterns that appear in trust and safety platform work: structured case ingestion, decision workflows with role-based enforcement, audit logging, and LLM-assisted moderation automation.

---

## Architecture

```
web/          React + TypeScript frontend (Vite, TanStack Query, Tailwind CSS)
api/          FastAPI backend (Python 3.12, SQLAlchemy async, asyncpg, Alembic)
ai_reviewer/  Polling CLI that classifies cases via Ollama or Claude API
docker-compose.yml  PostgreSQL 16
```

The frontend and the AI reviewer are both clients of the same REST API. A human analyst using the browser and an automated classifier running in the terminal post decisions through identical endpoints, which keeps the backend's surface area small and the audit log complete regardless of decision origin.

---

## Features

**Case queue.** Paginated table of all cases, filterable by category (toxic, severe toxic, obscene, threat, insult, identity hate), severity (high, medium, low), status, and date range. Categories follow the Jigsaw Toxic Comment Classification taxonomy.

**Case detail.** Full case content, decision history, and a decision form. Escalation is gated by role: the `reviewer` role can approve or reject, the `senior_reviewer` role can also escalate. The role is read from a request header, which lets the frontend inject the acting user's identity without a session system.

**Audit log.** Every decision recorded with actor ID, role, action, and timestamp. Filterable by actor and action. This is the same table the case detail view reads, and there is one write path for decisions regardless of who or what made them.

**AI reviewer.** A standalone CLI (`ai_reviewer run`) that polls the queue, fetches each pending case, and classifies it using a configurable large language model (LLM) backend. The Claude backend includes a cost guardrail that estimates spend per cycle and requires explicit confirmation before posting decisions. A `--dry-run` flag classifies without writing anything, which makes it safe to evaluate model behaviour before enabling live actioning.

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/cases` | Paginated case list with filters |
| `POST` | `/cases` | Ingest a new case |
| `GET` | `/cases/{id}` | Case detail with decision history |
| `POST` | `/cases/{id}/decisions` | Record a decision (role enforced) |
| `GET` | `/audit-log` | Paginated audit log with filters |

Responses follow a consistent `Page[T]` schema with `items`, `total`, `page`, and `page_size` fields.

---

## Setup

**Prerequisites:** Docker (for Postgres), Python 3.12 with [uv](https://docs.astral.sh/uv/), Node 18+ with pnpm.

```bash
# 1. Start Postgres
docker compose up -d

# 2. Backend
cd api
cp ../.env.example .env
uv sync
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/case_queue \
  uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000

# 3. Seed with synthetic cases (540 cases across 6 categories x 3 severities)
uv run python scripts/seed.py --confirm

# 4. Frontend (new terminal)
cd web
cp ../.env.example .env
pnpm install
pnpm dev   # http://localhost:5173
```

**AI reviewer (optional)**

```bash
cd ai_reviewer
uv sync
cp .env.example .env   # set OLLAMA_MODEL, CLAUDE_MODEL, etc.

uv run ai_reviewer run --backend ollama          # local model, no cost
uv run ai_reviewer run --backend claude          # Claude API (prompts for confirmation)
uv run ai_reviewer run --backend ollama --dry-run  # classify without posting decisions
```

**Tests**

```bash
# Backend (requires Postgres with case_queue_test DB)
cd api
createdb -U postgres case_queue_test   # one-time
uv run pytest -v   # 22 tests

# Frontend (no Postgres needed)
cd web
pnpm test          # 11 tests
```

---

## Design decisions

**Single write path for decisions.** The `POST /cases/{id}/decisions` endpoint is the only way a decision enters the system, whether it comes from the browser or the AI reviewer CLI. This means the audit log is always complete and the role enforcement logic lives in exactly one place. The alternative (separate endpoints for human and AI decisions) would have required duplicating the enforcement and the audit logic, with no corresponding benefit.

**Role enforcement via header, not session.** The acting user's ID and role arrive in `x-actor-id` and `x-actor-role` request headers. This is intentional for a portfolio tool: it avoids the complexity of an auth system while still modelling the shape of a real role-based access control policy. In a production deployment, these headers would be set by a gateway or middleware layer that validates the authenticated user's entitlements, not by the client.

**Async throughout, with NullPool in tests.** The API uses SQLAlchemy's async engine and asyncpg for non-blocking database access. Tests use a separate `case_queue_test` database with `NullPool` (no connection reuse across async contexts) and patch the lifespan `init_db` call so the test runner does not attempt to connect to the production database. Each test truncates tables in teardown rather than using transactions, which keeps isolation simple without requiring savepoint awareness.

**Alembic-only schema management.** The lifespan does not call `Base.metadata.create_all`. Schema changes go through Alembic migrations exclusively. Tests call `create_all` directly on the test database, which is appropriate because test setup is not a migration workflow. This keeps production and test paths clearly separate.

**AI reviewer confidence threshold.** The classifier requests a structured JSON response from the LLM containing the action, reasoning, and a confidence score. Cases below the threshold (`CONFIDENCE_THRESHOLD`, default 0.7) are escalated rather than approved or rejected, under the assumption that low-confidence automated decisions should route to a human. This means the AI reviewer naturally surfaces ambiguous content to the senior reviewer queue.

---

## Data

The seed script generates 540 synthetic cases (30 per category-severity bucket) using templates drawn from the Jigsaw Toxic Comment Classification categories. Content is synthetic but representative: each category has distinct linguistic patterns that reflect the real distribution (threats read differently from identity hate speech, which reads differently from obscenity). Severity is assigned by weighted random draw (high: 30%, medium: 45%, low: 25%) to approximate a realistic case load skewed toward moderate-confidence flags.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, TanStack Query, Tailwind CSS |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2 (async), asyncpg, Pydantic v2 |
| Database | PostgreSQL 16, Alembic migrations |
| AI reviewer | Typer CLI, httpx, Ollama (local), Claude API |
| Testing | pytest-asyncio, httpx ASGITransport, vitest, Testing Library |
| Tooling | uv, pnpm, ruff, Docker Compose |
