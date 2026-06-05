# Brief Output — moderation-dashboard demo hardening

**Role:** brief
**Sequence:** planner → architect → implementer
**Date:** 2026-06-04

---

## Project Name

`moderation-dashboard-demo`

---

## Description

A demo hardening pass on the completed moderation-dashboard: make it deployable as a live public portfolio demo where visitors see a real Kafka-backed content moderation stream running 2 live ML models, historical metrics pre-seeded for 3 additional models, case escalations flowing to a built-in review queue, and analytics populated — all on a $4/month VPS.

---

## Language(s)

- **Python** — FastAPI (API additions), seeding script, consumer changes
- **TypeScript / React** — dashboard UI improvements
- **SQL** — schema additions, seed data

---

## Background: What Is Already Built

The moderation-dashboard (`projects/moderation-dashboard/`) is complete and running locally. It includes:

- **Kafka** (`apache/kafka:3.7.0` KRaft, port 9093) — working, connectivity confirmed
- **Postgres** (port 5434) — schema migrated, tables present
- **Producer** (`md-producer`) — streams Jigsaw CSV events to `moderation-events` topic
- **Consumers** (`md-consumer`) — DistilBERT, RoBERTa, Detoxify (zero-shot); fine-tuned DistilBERT and RoBERTa (activated via `DISTILBERT_CHECKPOINT_PATH` / `ROBERTA_CHECKPOINT_PATH` env vars)
- **FastAPI metrics API** (`md-api`, port 8002) — `/metrics`, `/health`, `/metrics/analytics`
- **Anomaly detector** (`md-anomaly`) and **escalation service** (`md-escalation`)
- **React frontend** (`web/`, port 5174) — Stream Monitor, Model Performance, Model Comparison, Human Review, Analytics panels
- **Fine-tuned checkpoints** — `resources/models/toxicity-classifier-finetuned/distilbert-best` (F1=0.8473) and `resources/models/toxicity-classifier-finetuned/roberta-best` (F1=0.8424, 1 epoch)

**Known issues with current dashboard (to fix in this pass):**
- Sparklines are flat with no labels — visitors don't know what metric they're looking at or what constitutes good/bad
- Round-robin routing only shows one model's results in the production panel despite 3 consumers active (likely partition/group config issue)
- Stream Monitor lacks a time-series line chart — only shows current snapshot stats
- Analytics tab empty — dbt mart tables not populated; no dbt runtime planned for hosted deployment
- Escalation service not wired to case-queue — fires events internally but doesn't POST to any external endpoint

---

## The Demo Vision

When a visitor arrives at the hosted site they should see:

1. **A live event stream** — Jigsaw comments flowing through the system in real-time, classified by models
2. **Model metrics** that are non-zero on arrival — not starting from scratch
3. **All 5 models showing data** — 2 running live, 3 showing pre-seeded historical metrics
4. **A case queue** — escalated events accumulating, actionable (approve/reject) during the visit
5. **Analytics** — category trends, model accuracy over time, enforcement rates
6. **A restart button** — replays the stream from the beginning

Each visitor sees a continuously running stream. On arrival the stream is already mid-run (pre-seeded historical data gives non-zero baselines). The live models keep classifying new events throughout the visit.

---

## Architecture Decisions (already made — do not re-open)

**1. Two live models, three seeded.**

On the hosted server, only DistilBERT zero-shot and Detoxify run as live consumers. Their classifications accumulate in real-time. The other three models — RoBERTa zero-shot, fine-tuned DistilBERT, fine-tuned RoBERTa — have their classifications pre-seeded into the DB via a one-time seed script run locally before deploy. Their metrics show correctly in the dashboard; they just don't process new events.

Memory budget (Hetzner CX22, 4GB RAM):
- DistilBERT consumer: ~260MB
- Detoxify consumer: ~270MB
- Kafka: ~400MB
- Postgres: ~200MB
- API + anomaly + escalation: ~150MB
- **Total: ~1.3GB** — comfortable on 4GB

**2. Looping producer.**

The producer runs on a subset (~10k events) and loops continuously. This keeps the stream perpetually live. Historical data from previous loops accumulates in the DB, making metrics progressively richer over time.

**3. Pre-seeded historical data.**

A local seed script (`scripts/seed_sim.py`) runs all 5 models over the 10k-event subset, writes classifications to the DB, and marks them with a `seeded=true` flag so they can be distinguished from live results. This script is run once before deploy; its output is loaded into the hosted Postgres via pg_dump/restore.

**4. Built-in case queue panel.**

Rather than depending on the separate `projects/case-queue/` service for the demo, a lightweight case queue is built directly into the moderation-dashboard. The "Human Review" panel shows escalated events with approve/reject buttons. Decisions are stored in a `case_decisions` table within the moderation-dashboard DB. In production, the escalation service would POST to the real case-queue API — this is a `CASE_QUEUE_URL` env var that can be set to enable the real integration. For the demo, it falls back to the built-in panel.

**5. Analytics from DB aggregates, not dbt.**

The analytics tab is populated via SQL aggregates computed by the FastAPI API directly (no dbt runtime required). The `/metrics/analytics` endpoint is extended to return time-series data computed from the `classifications` table. dbt remains in the codebase for local dev / real deployments but is not required for the hosted demo.

**6. No simulation mode / DEMO_MODE flag.**

The system runs as a real Kafka streaming pipeline, not a simulation. The only "demo" mechanics are: (a) pre-seeded historical data for 3 models, (b) the looping producer, and (c) a restart endpoint that truncates live classifications and restarts the producer from event 0. This keeps the architecture genuine.

**7. Deploy target: Hetzner CX22.**

~$4.35/month, 4GB RAM, 2 vCPU, 40GB NVMe. Docker Compose + nginx reverse proxy. React built to static files, served by nginx. FastAPI behind nginx at `/api`. Kafka and Postgres internal to Docker network.

---

## Success Criteria

This pass is done when all of the following are true:

1. **Seed script** — `scripts/seed_sim.py` classifies 10k Jigsaw events with all 5 models and writes results to the DB. Runs locally in under 30 minutes. Produces a pg_dump file ready for VPS restore.

2. **Looping producer** — `md-producer` accepts a `--loop` flag. When set, it replays the 10k-event subset continuously. Producer restart can be triggered via `POST /admin/restart` API endpoint (clears live classifications, resets producer offset).

3. **All 5 models visible** — Dashboard shows metrics for all 5 models. DistilBERT and Detoxify show live counters incrementing. RoBERTa, fine-tuned DistilBERT, fine-tuned RoBERTa show seeded historical metrics that do not increment (clearly distinguished in UI — e.g., "Historical" badge vs "Live" badge).

4. **Sparklines** — each model metrics card has a labelled sparkline showing the metric trend over the last N events. Label states the metric name and current value. A reference line shows the zero-shot baseline for comparison on the fine-tuned cards.

5. **Stream monitor time-series** — a line chart showing event volume by category over the last 10 minutes (or since stream start, whichever is shorter). Updates on each poll.

6. **Analytics tab populated** — shows category trend chart, per-model accuracy over time, and escalation rate. Computed from DB aggregates, no dbt required.

7. **Case queue** — escalated events (confidence < 0.6 OR model disagreement) appear in Human Review panel. Approve/reject buttons write to `case_decisions` table. Decision state persists within the session. Panel shows pending count badge.

8. **Restart button** — calls `POST /admin/restart`. Truncates live (non-seeded) classifications and anomaly flags. Restarts the producer from event 0. Dashboard reflects reset within 3 seconds.

9. **Live/Historical distinction** — UI clearly distinguishes live model results from pre-seeded historical results. Suggested: a "LIVE" green indicator on active consumers, a "SEEDED" grey badge on historical models.

10. **Deployed to Hetzner** — site accessible at a public URL. Docker Compose running. nginx serving React static build and proxying API. Kafka and Postgres persisted via named volumes.

11. **README updated** — local run guide, deploy guide (Hetzner), seed script usage, environment variable reference.

---

## Constraints

- **No dbt runtime on hosted deployment** — analytics computed via SQL in FastAPI; dbt stays in the repo for local use only
- **No case-queue dependency for demo** — built-in case panel must work standalone; `CASE_QUEUE_URL` env var optionally enables real integration
- **CPU inference only** — no CUDA, no MPS on Hetzner; all model inference at `device=-1`
- **4GB RAM ceiling** — total memory footprint of all running services must stay under 3GB to leave headroom
- **Kafka must persist across restarts** — named Docker volume required; current config uses `/tmp/kraft-combined-logs` which must be fixed
- **Restart must not affect seeded data** — `POST /admin/restart` truncates only rows where `seeded=false`
- **Fine-tuned model checkpoints are not deployed** — too large (500MB each) for a $4 VPS image; fine-tuned consumers remain stubbed with `pending_weights` status on hosted deployment unless checkpoints are pre-downloaded to a mounted volume

---

## Out of Scope

- Running fine-tuned consumers live on the hosted deployment (resource constraint; seeded data covers their metrics)
- Replacing or modifying the `projects/case-queue/` codebase
- WebSocket or SSE (polling continues at 3s)
- Authentication or per-user sessions
- dbt runtime on the VPS
- Anomaly detector changes (it runs as-is; anomaly flags surface in the existing Stream Monitor panel)
- CI/CD pipeline (manual deploy via SSH + docker compose pull is sufficient for portfolio)

---

## Assumptions

1. The 10k-event subset is drawn from the same Jigsaw train.csv at `resources/datasets/jigsaw-toxic-comments/train.csv`, rows 0–9999.
2. The seed script runs all 5 models at `device=-1` (CPU). On M4 Air this takes ~20–30 minutes. It writes directly to a local Postgres instance at the project's standard port (5434).
3. The `classifications` table already has a `model_name` column that distinguishes which consumer wrote each row. A `seeded` boolean column needs to be added (Alembic migration).
4. The looping producer runs the 10k-event subset; larger event content variety isn't needed for demo purposes.
5. Hetzner account needs to be created; SSH key configured. Standard Ubuntu 24.04 image. Docker + Docker Compose installed via setup script.
6. The "restart" mechanic is global — one visitor triggering restart affects all concurrent visitors. Accepted tradeoff for simplicity (no session isolation in the live system).
7. Sparkline data comes from the last 50 classification events per model (configurable), stored in the existing `classifications` table.

---

## Handoff

**Next role:** planner

**What the planner does with this:**
- Define the complete list of file changes: new files, modified files, new DB columns, new API endpoints
- Spec the `seeded` column migration and confirm it doesn't break existing queries
- Define the seed script architecture: one pass per model or batched; output format
- Lock the looping producer implementation: how offset/position is tracked across loops
- Spec the `POST /admin/restart` endpoint: what it truncates, how it signals the producer
- Define the sparkline data contract: what the API returns, how the frontend renders it
- Spec the time-series stream chart data structure
- Spec the analytics endpoint extensions (what SQL, what shape)
- Define the case queue data flow: escalation service → `case_decisions` table → Human Review panel
- Define the Hetzner deploy steps: Docker Compose changes (Kafka volume, nginx service), seed restore procedure
- Identify all files that need to change and flag any that are risky to touch (e.g. existing migrations)

**Flags for planner:**
- The current Kafka `KAFKA_LOG_DIRS` is set to `/tmp/kraft-combined-logs` — this must be changed to a named volume before deploy or all Kafka data is lost on restart. This is a docker-compose change.
- The fine-tuned consumers read checkpoint paths from env vars. On Hetzner these vars will not be set, so the consumers will show `pending_weights`. Confirm this graceful degradation is already implemented and test it.
- The existing escalation service fires internally but its POST logic needs to be confirmed: does it currently write to the DB, to case-queue API, or both? This determines how much wiring is actually new work.
- Round-robin routing showing only one model is a known bug — planner must diagnose (likely a partition count issue: if the `moderation-events` topic has fewer partitions than production consumers, some consumers sit idle). Fixing this is in scope.
