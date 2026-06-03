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
| Frontend code | ✓ Complete | React 18, TypeScript, TanStack Query, shadcn/ui, Tailwind CSS |
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

### How to Deploy (not yet done)

**Deployment target: Hostinger VPS (API + frontend via nginx) + public GitHub repository.**

The existing `api/Dockerfile` and `docker-compose.yml` are the correct deployment artifacts for Hostinger. The `api/fly.toml` is Fly.io-specific and can be ignored.

**Step 1 — Push to public GitHub repo**
```bash
gh repo create case-queue --public --source=projects/case-queue --push
```

**Step 2 — Hostinger VPS setup**
SSH into the Hostinger VPS, then:
```bash
# Clone from GitHub
git clone https://github.com/YOUR-USERNAME/case-queue.git
cd case-queue

# Configure environment
cp .env.example .env
# Edit .env: set DATABASE_URL, ALLOWED_ORIGINS, VITE_API_URL to VPS hostname

# Start API + Postgres
docker compose up -d

# Run migrations
docker compose exec api uv run alembic upgrade head

# Seed data (one-time)
docker compose exec api uv run python scripts/seed.py --confirm
```

**Step 3 — Build and serve frontend via nginx**
```bash
cd web
pnpm install && pnpm build
# dist/ contains the static build — serve via nginx
```

Configure nginx as a reverse proxy:
- `/api/*` → `localhost:8000` (FastAPI)
- `/*` → static files from `web/dist/`

**Step 4 — Update README and one-pager**
Replace `projects/case-queue/` path references with live GitHub URL and Hostinger hostname.

### Next Steps

1. **Create public GitHub repo and push** — unblocks the live demo and makes the portfolio piece verifiable.
2. **Deploy to Hostinger VPS** — follow the steps above.
3. **Update ALLOWED_ORIGINS** in `.env` once the Hostinger hostname is confirmed.

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

## Project 22 — Content Moderation Event Stream and Model Comparison Platform

**Last updated:** 2026-06-03
**Location:** `projects/moderation-stream/` (frontend additions in `projects/case-queue/web/src/`)
**Proposal target:** Both (SWE and DE Safeguards)
**Stack:** Python 3.12 (FastAPI, confluent-kafka, transformers, SQLAlchemy), TypeScript (React, TanStack Query), Kafka, PostgreSQL (port 5433)

### Current State

| Item | Status | Notes |
|---|---|---|
| Kafka producer | ✓ Complete | Replays Jigsaw CSV at configurable rate; rate limiting; SIGINT shutdown |
| Phase 1 consumers (3) | ✓ Complete | DistilBERT zero-shot, RoBERTa zero-shot, Detoxify |
| Phase 2 consumers (2) | ✓ Stubbed | Fine-tuned DistilBERT + RoBERTa; exit cleanly with no checkpoint; activate via config |
| Metrics API | ✓ Complete | FastAPI on port 8001; GROUP BY SQL with percentile_cont; GET /metrics, GET /health |
| React dashboard | ✓ Complete | `/stream` route in case-queue; 5-card grid; 3s polling; skeleton/error states; time series charts |
| Time series charts | ✓ Complete | Accuracy + latency (p50/p95) sparklines per active card; 30-point rolling history in StreamDashboard |
| SQL cast bug | ✓ Fixed | `correct::float` → `correct::int::float` (PostgreSQL boolean→float requires intermediate int cast) |
| README.md | ✓ Added | Was missing; caused hatchling build failure on `uv run` |
| Backend tests | ✓ 17/17 | 7 unit (producer + consumers, infra-free), 7 API integration (shape + computation) |
| Frontend tests | ✓ 21/21 | Includes ModelMetricsCard (6) and StreamDashboard (4) — chart tests not yet written |
| Technical summary | ✓ Written | `projects/moderation-stream/docs/technical-summary.md` |
| Phase 2 weights | ✗ Pending | Requires project 8 (fine-tuned DistilBERT + RoBERTa checkpoints) |
| Alembic migrations | ✗ Deferred | Using `create_all` for now; straightforward to add before production deploy |
| Jigsaw CSV | ✗ Not on machine | Producer requires real `train.csv`; synthetic CSV used for local dev only |
| Live deploy | ✗ | Deploys alongside case-queue on Hostinger VPS |

### How to Run Locally

**Prerequisites:** Docker running, `brew install librdkafka`, uv installed.

```bash
cd projects/moderation-stream

# 1. Start infrastructure
docker compose up -d   # Kafka + Zookeeper + Postgres on 5433
uv sync
cp .env.example .env   # edit JIGSAW_CSV_PATH to point at your Jigsaw train.csv

# 2. Run (3 terminals or make all)
make api        # metrics API on :8001
make consumers  # 3 Phase 1 consumers
make producer   # publish 1000 events at 10/sec

# 3. Frontend (from case-queue/web, after adding VITE_STREAM_API_URL=http://localhost:8001 to .env)
pnpm dev        # visit http://localhost:5173/stream
```

### How to Test

```bash
cd projects/moderation-stream

# Unit tests (no infra needed)
uv run pytest tests/test_producer.py tests/test_consumers.py -v

# API integration tests (requires Postgres on 5433)
createdb -U postgres -p 5433 moderation_stream_test   # one-time
uv run pytest tests/test_api.py -v

# Frontend tests (from case-queue/web)
cd ../case-queue/web && npx vitest run
```

### How to Deploy (not yet done)

Deploys to the same Hostinger VPS as case-queue. Add as additional services in the VPS docker-compose or run separately.

```bash
# On Hostinger VPS — after case-queue is deployed
git clone https://github.com/YOUR-USERNAME/moderation-stream.git
cd moderation-stream
cp .env.example .env   # set JIGSAW_CSV_PATH, DATABASE_URL pointing to Postgres on 5433
docker compose up -d
```

nginx: proxy `/stream-api/*` → `localhost:8001`.

### Next Steps

1. **Deploy to Hostinger** — alongside case-queue; follow steps above. Requires real Jigsaw `train.csv` on the VPS for the producer to run.
2. **Add real Jigsaw CSV** — download from Kaggle; place at `data/train.csv` (gitignored). The synthetic CSV in `data/` is local-dev only.
3. **Project 8 checkpoints** — drop fine-tuned weights into config to activate Phase 2.
4. **Alembic migration** — run `alembic revision --autogenerate -m "initial"` against live DB before first deploy.
5. **Chart tests** — `ModelMetricsCard` and `StreamDashboard` tests do not yet cover the recharts sparklines; add tests once chart behaviour is stable.

---

## Project 8 — Fine-Tuned Toxicity Classifier

**Last updated:** 2026-06-03
**Location:** `projects/toxicity-classifier-finetuned/`
**Branch:** merged to `main`
**Proposal target:** Both (SWE and DE Safeguards)
**Stack:** Python 3.12, PyTorch, HuggingFace transformers + datasets, scikit-learn, Typer CLI

### Current State

| Item | Status | Notes |
|---|---|---|
| Data pipeline (`data.py`) | ✓ Complete | Stratified 80/10/10 split; tokenisation with category column retention |
| DistilBERT training (`train_distilbert.py`) | ✓ Complete | `distilbert-base-uncased`; Trainer; saves `distilbert-best/` |
| RoBERTa training (`train_roberta.py`) | ✓ Complete | `roberta-base`; default batch=16 (MPS memory); saves `roberta-best/` |
| Evaluation (`evaluate.py`) | ✓ Complete | Fine-tuned vs zero-shot; per-category accuracy; JSON + stdout table |
| CLI entry points | ✓ Complete | `uv run train --model distilbert` / `uv run evaluate --model distilbert` |
| Colab notebook | ✓ Complete | `notebooks/colab_training.ipynb` — T4/A100, Drive checkpoint persistence |
| Tests | ✓ 16/16 | No live weight downloads; mocked architectures |
| README | ✓ Written | Dataset download, training commands, Colab, project 22 integration |
| Experiment doc | ✗ Pending | Write after training run completes — zero-shot vs fine-tuned comparison |
| Model weights (distilbert-best/) | ✗ Not produced | Requires Jigsaw download + training run |
| Model weights (roberta-best/) | ✗ Not produced | Requires Jigsaw download + training run |
| Project 22 Phase 2 activated | ✗ Pending | Set env vars once weights produced |
| Portfolio write-doc (technical summary) | ✗ Pending | Run `write-doc` sequence post-training; audience: Technical / Technical Leadership |

### Training Plan

**Step 0 — Get the dataset**

Download `train.csv` from the [Jigsaw Toxic Comments Classification Challenge](https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge) on Kaggle (free, requires account). Place it at `data/train.csv` inside the project, or set `JIGSAW_DATA_DIR` in `.env` to an absolute path. The same CSV doubles as the producer input for moderation-stream — copy it to `projects/moderation-stream/data/train.csv` at the same time.

**Step 1 — Choose local or Colab**

| Option | Time | Cost | Recommendation |
|---|---|---|---|
| Local MPS (Apple Silicon) | ~40–50 min DistilBERT, ~60–80 min RoBERTa | Free | Good if not time-constrained; keeps weights on local disk |
| Colab T4 | ~15–20 min per model | ~$1–2 total | Faster; use the notebook at `notebooks/colab_training.ipynb`; save weights to Google Drive then download |
| Local CPU | ~3–5 hours per model | Free | Not recommended |

**Step 2 — Run training**

```bash
cd projects/toxicity-classifier-finetuned
export PATH="$HOME/.local/bin:$PATH"
cp .env.example .env
# Edit .env: set JIGSAW_DATA_DIR=data  (relative, or absolute path)

uv sync

# Smoke test first (~5 min, confirms the pipeline works end-to-end)
uv run train --model distilbert --epochs 1 --max-train-samples 2000

# Full DistilBERT (4 epochs, all data)
uv run train --model distilbert --epochs 4

# Full RoBERTa (reduce batch if MPS runs out of memory)
uv run train --model roberta --epochs 4 --batch-size 8
```

**Step 3 — What training produces**

```
checkpoints/
  distilbert-best/        ← best val-F1 epoch; ~250MB on disk
    config.json
    model.safetensors
    tokenizer.json / vocab.txt / ...
  roberta-best/           ← same structure; ~480MB on disk
  distilbert-train-log.json   ← per-epoch loss + val F1 (for experiment doc)
  roberta-train-log.json
```

Training picks the best epoch automatically (`load_best_model_at_end=True`, metric=F1). No manual checkpoint selection needed.

**Expected results (reference targets)**

| Model | Zero-shot F1 | Fine-tuned F1 target |
|---|---|---|
| DistilBERT | ~0.55–0.65 | ~0.89–0.92 |
| RoBERTa | ~0.55–0.65 | ~0.91–0.94 |

If fine-tuned F1 is below 0.85 after 4 epochs, check: class imbalance in splits, learning rate too high, or CSV encoding issues.

### How to Evaluate

```bash
cd projects/toxicity-classifier-finetuned
uv run evaluate --model distilbert --checkpoint-dir checkpoints/distilbert-best
uv run evaluate --model roberta --checkpoint-dir checkpoints/roberta-best
# JSON results written to eval_results/; summary table printed to stdout
```

### How to Test

```bash
cd projects/toxicity-classifier-finetuned
uv run pytest -v   # 16 tests, no weight downloads
uv run ruff check .
```

### How to Activate Project 22 Phase 2

Once checkpoints are trained, add to `projects/moderation-stream/.env`:

```bash
DISTILBERT_CHECKPOINT_PATH=/absolute/path/to/checkpoints/distilbert-best
ROBERTA_CHECKPOINT_PATH=/absolute/path/to/checkpoints/roberta-best
```

Restart the fine-tuned consumers (`make all`). Slots 4 and 5 in the stream dashboard switch from `pending_weights` to `active` — no code changes.

### Next Steps

1. **Download Jigsaw CSV** — place at `data/train.csv` and copy to `projects/moderation-stream/data/train.csv` simultaneously. Unblocks both training and the stream producer.
2. **Run smoke test** — `uv run train --model distilbert --epochs 1 --max-train-samples 2000`. Confirms pipeline works before committing to a full run.
3. **Run full training** — DistilBERT then RoBERTa (see Training Plan above). Local MPS or Colab T4.
4. **Evaluate** — `uv run evaluate --model distilbert --checkpoint-dir checkpoints/distilbert-best` and RoBERTa equivalent. Check F1 ≥ 0.85 before proceeding.
5. **Activate project 22 Phase 2** — set `DISTILBERT_CHECKPOINT_PATH` / `ROBERTA_CHECKPOINT_PATH` in `projects/moderation-stream/.env`; restart consumers; verify stream dashboard shows 5 active cards.
6. **Write experiment doc** — `docs/experiment-results.md`: zero-shot vs fine-tuned F1 per model, per-category breakdown, failure modes. Portfolio evidence of ML reasoning.
7. **Run `write-doc` sequence** — technical summary for portfolio. Audience: Technical. Inputs: experiment doc + README + eval results JSON.

---

## Status Summary

| # | Project | Code | Tests | Docs | Deploy/Published | Immediate next action |
|---|---|---|---|---|---|---|
| 21 | Case Queue | ✓ | ✓ 22/22 | ✓ | Not live | Push to public GitHub + deploy to Hostinger VPS |
| 2 | Eval Harness | ✓ | ✓ 45/45 | ✓ | Held | Publish to GitHub after case-queue is live |
| 22 | Moderation Stream | ✓ | ✓ 21/21 | ✓ | Not live | Deploy to Hostinger alongside case-queue |
| 8 | Toxicity Classifier (fine-tuned) | ✓ | ✓ 16/16 | Partial | Not started | Download Jigsaw + run training; write experiment doc; activate project 22 Phase 2 |

---

## Environment Reference

| Tool | Status | Notes |
|---|---|---|
| Docker | Running | `case-queue-postgres-1` container healthy on port 5432 |
| Ollama | Running | `gemma2:9b` and `qwen2.5-coder:7b` available |
| uv | Installed | `~/.local/bin/uv` |
| pnpm | Installed | v11.5.0, `/opt/homebrew/bin/node` v26.0.0 |
| `ANTHROPIC_API_KEY` | Set | Required for LLM-as-judge scoring in eval-harness and Claude backend in ai_reviewer |
