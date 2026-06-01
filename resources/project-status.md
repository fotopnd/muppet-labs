# project-status.md — Muppet Labs Portfolio Tracker

> Tracks delivered state, open next steps, and run instructions for each project.
> Updated after each review session. Read this first in any new session touching a project.

---

## Project 21 — Case Queue and Content Review Tool

**Last updated:** 2026-06-01
**Location:** `projects/case-queue/`
**Proposal target:** Software Engineer, Safeguards Foundations
**Stack:** React/TypeScript (Vite), FastAPI (Python 3.12), PostgreSQL 16, Docker

### Current State

| Item | Status | Notes |
|---|---|---|
| Backend code | ✓ Complete | FastAPI, SQLAlchemy async, asyncpg, Alembic |
| Frontend code | ✓ Complete | React 18, TypeScript, TanStack Query, Tailwind CSS |
| `ai_reviewer` CLI | ✓ Complete | Polls queue, classifies via Ollama or Claude API |
| Backend tests | ✓ 22/22 | pytest-asyncio, NullPool, lifespan patched |
| Frontend tests | ✓ 11/11 | vitest, Testing Library |
| Alembic migration | ✓ At head | `715088b8a08a_initial` applied to local DB |
| Seed data | ✓ Verified | 540 cases, 6 Jigsaw categories × 3 severities, realistic content |
| Portfolio README | ✓ Written | `projects/case-queue/README.md` — architecture, design decisions, setup |
| Fly.io config | ✓ Ready | `api/Dockerfile`, `api/fly.toml`, `api/.dockerignore` — **not yet deployed** |
| Vercel config | ✓ Ready | `web/vercel.json` — **not yet deployed** |
| Live URL | ✗ | Deployment commands ready but not run — see Deploy section below |

### How to Run Locally

**Prerequisites:** Docker running, uv installed (`~/.local/bin/uv`), pnpm installed.

```bash
# 1. Start Postgres
cd projects/case-queue
docker compose up -d

# 2. API (terminal 1)
cd projects/case-queue/api
uv sync
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/case_queue \
  uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
# API at http://localhost:8000  |  Docs at http://localhost:8000/docs

# 3. Seed data (one-time, separate terminal)
cd projects/case-queue/api
uv run python scripts/seed.py --confirm

# 4. Frontend (terminal 2)
cd projects/case-queue/web
pnpm install
pnpm dev
# UI at http://localhost:5173

# 5. AI reviewer (optional, terminal 3)
cd projects/case-queue/ai_reviewer
uv sync
uv run ai_reviewer run --backend ollama --dry-run
```

### How to Test

```bash
# Backend (requires Postgres running)
cd projects/case-queue/api
createdb -U postgres case_queue_test   # one-time only
uv run pytest -v                       # 22 tests

# Frontend (no Postgres needed)
cd projects/case-queue/web
pnpm test                              # 11 tests
```

### How to Deploy (not yet done — run these commands)

**Step 1 — Fly.io (API)**
```bash
# Install CLI
brew install flyctl
fly auth login

cd projects/case-queue/api
fly launch --no-deploy
# Answer prompts: choose app name, confirm lhr region, YES to Postgres
# fly.toml is already present — it will update the app name in place

fly secrets set ALLOWED_ORIGINS="https://YOUR-VERCEL-URL.vercel.app"
fly deploy
# Migrations run automatically via release_command before each deploy
```

**Step 2 — Vercel (Frontend)**
```bash
pnpm install -g vercel
vercel login

cd projects/case-queue/web
vercel env add VITE_API_URL            # enter: https://YOUR-APP-NAME.fly.dev
vercel env add VITE_ACTOR_ID           # enter: dev-user
vercel env add VITE_ACTOR_ROLE         # enter: senior_reviewer
vercel deploy --prod
```

**Step 3 — Update fly.toml**
After `fly launch` assigns an app name, update the `app = 'YOUR-APP-NAME'` line in `api/fly.toml` and commit.

### Next Steps

1. **Deploy** — run the commands above. Unblocks the live demo.
2. **Add Vercel URL to ALLOWED_ORIGINS on Fly** — one `fly secrets set` command after both are live.
3. **shadcn/ui (optional)** — visual polish; not a portfolio blocker.

---

## Project 2 — Model Behaviour Evaluation Harness

**Last updated:** 2026-06-01
**Location:** `projects/eval-harness/`
**Proposal target:** Both (SWE and DE Safeguards)
**Stack:** Python 3.12, SQLite, Typer CLI, Rich

### Current State

| Item | Status | Notes |
|---|---|---|
| Core harness | ✓ Complete | `eval run`, `eval diff`, `eval list`, `eval add-case` |
| Datasets | ✓ Complete | TruthfulQA (HuggingFace), AdvBench (HuggingFace + CSV fallback), custom YAML |
| Rubrics | ✓ Complete | `refusal_detection`, `truthfulness`, `harmlessness` YAML rubrics |
| LLM-as-judge scoring | ✓ Complete | Claude via Anthropic SDK, heuristic fallback |
| Drift detection | ✓ Complete | Per-rubric, per-dataset deltas, flip detection |
| Tests | ✓ 45 tests | Scorer, drift, DB roundtrip, datasets, runner |
| Portfolio one-pager | ✓ Written | `docs/one-pager.md` |
| README | ✓ Written | Setup, config, command reference |
| Baseline eval results | ✓ Committed | `runs/` — qwen2.5-coder:7b vs gemma2:9b on AdvBench (25 cases each, 1.000 refusal accuracy both) |
| Model defaults | ✓ Updated | `gemma2:9b` = default/conversational, `qwen2.5-coder:7b` = coder; `qwen3-coder-30b` hard-blocked |
| Published to GitHub | ✗ | Held until portfolio is stable |

### How to Run

```bash
cd projects/eval-harness

# Install
uv sync

# Run against local Ollama model (Ollama must be running)
uv run eval run --model default --dataset advbench --limit 10 --no-judge

# Run with LLM-as-judge (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=...
uv run eval run --model default --dataset advbench --limit 5

# Compare two runs
uv run eval diff baseline-qwen2.5-coder-7b baseline-gemma2-9b

# List all runs
uv run eval list
```

### How to Test

```bash
cd projects/eval-harness
uv run pytest -v   # 45 tests, no external services needed
```

### Model Aliases (models.yaml)

| Alias | Model | Use case |
|---|---|---|
| `default` | gemma2:9b | Conversational tasks, classification, review |
| `coder` | qwen2.5-coder:7b | Code generation, completion |
| `mlx-default` | mlx-community/gemma-2-9b-it-4bit | MLX server on Apple Silicon |
| `mlx-coder` | mlx-community/Qwen2.5-Coder-7B-Instruct-4bit | MLX coder on Apple Silicon |
| `haiku` / `sonnet` / `opus` | Claude models | Cloud inference |
| `qwen3-coder-30b` | — | **BLOCKED** — triggers RuntimeError |

### Next Steps

1. **Publish to GitHub** — when portfolio is stable and ready to share
2. **Add custom safety test suite** — hand-authored YAML cases for trust & safety domain knowledge signal
3. **Consider `eval serve`** — minimal web view for run history and drift reports (optional differentiator)

---

## Status Summary

| # | Project | Code | Tests | Docs | Deploy/Published | Immediate next action |
|---|---|---|---|---|---|---|
| 21 | Case Queue | ✓ | ✓ 22/22 | ✓ | Config ready, not live | Run `fly launch` + `vercel deploy` |
| 2 | Eval Harness | ✓ | ✓ 45/45 | ✓ | Held | Publish to GitHub when portfolio ready |

---

## Environment Reference

| Tool | Status | Notes |
|---|---|---|
| Docker | Running | `case-queue-postgres-1` container healthy on port 5432 |
| Ollama | Running | `gemma2:9b` and `qwen2.5-coder:7b` available |
| uv | Installed | `~/.local/bin/uv` |
| pnpm | Installed | v11.5.0, `/opt/homebrew/bin/node` v26.0.0 |
| `ANTHROPIC_API_KEY` | Set | Required for LLM-as-judge scoring in eval-harness and Claude backend in ai_reviewer |
