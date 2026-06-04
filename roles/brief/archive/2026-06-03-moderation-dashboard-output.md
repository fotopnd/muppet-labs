# Brief Output — moderation-dashboard

**Role:** brief
**Sequence:** `new-project-full` (step 1)
**Date:** 2026-06-03

---

## Project Name

`moderation-dashboard`

---

## Description

A unified content moderation platform that streams Jigsaw Toxic Comments through Kafka, routes events to N attached models via both round-robin production routing and parallel shadow evaluation simultaneously, surfaces per-model performance metrics and head-to-head comparisons, detects anomalies on the raw event stream, transforms results through dbt for rolling analytics, and escalates low-confidence cases to the case-queue service for human review.

---

## Language(s)

- **Primary:** Python (FastAPI metrics API, Kafka producer and consumers, anomaly detector)
- **Analytics:** dbt-core with dbt-postgres adapter (SQL transformation layer)
- **Frontend:** TypeScript, React (unified dashboard — new app, separate from case-queue web/)

---

## Success Criteria

The project is done (Phase 1) when all of the following are true:

1. **Producer** — replays Jigsaw Toxic Comments CSV as a live Kafka stream at configurable rate; SIGINT shutdown.
2. **Production consumer group** — 3 zero-shot models (DistilBERT, RoBERTa, Detoxify) in the same Kafka consumer group; Kafka round-robins events across them. Per-model metrics recorded: F1 vs ground truth, latency p50/p95, throughput (events/sec).
3. **Shadow consumer group** — same 3 models each in separate consumer groups; every event hits every model. Per-event model verdicts recorded for comparison.
4. **Anomaly detector** — monitors raw event stream on rolling 5-minute windows; flags: volume spikes (Z-score > 3), per-category classification rate shifts, model disagreement rate anomalies. Flagged events surfaced in Stream Monitor.
5. **dbt layer** — dbt-core models run on the Postgres event store; analytical models cover: category trends over time, per-model accuracy rolling windows, escalation rates. Refreshed on a schedule (Makefile target or cron, not real-time).
6. **Escalation** — events where shadow models disagree (majority verdict ≠ unanimous) OR max softmax confidence < 0.6 are posted to case-queue API. Escalation threshold is configurable via env var.
7. **Dashboard — 5 panels:**
   - Stream Monitor: raw event rate, category distribution, anomaly flags
   - Model Performance: round-robin per-model F1, latency, throughput (production group metrics)
   - Model Comparison: side-by-side shadow group verdicts on identical events; accuracy delta
   - Human Review: escalation queue pulling from case-queue API; links to case-queue detail view
   - Analytics: dbt output — category trends, enforcement rates, model accuracy over time
8. **Phase 2 consumers** — fine-tuned DistilBERT and RoBERTa consumers stubbed; activate via `DISTILBERT_CHECKPOINT_PATH` and `ROBERTA_CHECKPOINT_PATH` env vars when project 8 delivers weights. No code change required to activate.
9. **Tests** — producer unit tests, consumer classification tests (mocked weights), anomaly detector unit tests, metrics API integration tests, dbt model tests (`dbt test`), frontend component tests (vitest).
10. **README** — local run instructions (Docker, uv, pnpm), dbt setup, Hostinger deploy guide.

---

## Constraints

- **Hostinger KVM2 (8GB RAM):** 5 transformer models (CPU inference) + Kafka + Zookeeper + Postgres + API + nginx must fit within 8GB. Models must load lazily — only the consumers actively assigned events load their weights at startup. Phase 1 max: 3 models in memory simultaneously.
- **CPU inference only on server:** no CUDA or MPS dependency in production path. Target <100ms per classification on CPU (relaxed from project 22's 5–50ms — Hostinger CPU is slower than M4).
- **Case-queue dependency:** escalation integration requires case-queue API to be running. Local dev: case-queue on `localhost:8000`. Production: case-queue deployed to same VPS. Dashboard degrades gracefully if case-queue is unavailable (Human Review panel shows error state, stream continues).
- **Phase 2 is blocked on project 8 RoBERTa:** fine-tuned consumers are stubs at launch. Phase 2 is a config change, not a code change.
- **Reuse project 22 code:** producer, consumer base class, model consumer implementations, and metrics API are the starting point. This is a refactor and extension, not a greenfield build.
- **Port allocation (local dev):**
  - Kafka: 9092 (existing)
  - Postgres: 5434 (5432 = case-queue, 5433 = moderation-stream during transition)
  - Metrics API: 8002 (8000 = case-queue, 8001 = moderation-stream)
  - Frontend dev: 5174 (5173 = case-queue web)

---

## Out of Scope

- Fine-tuning models (project 8 handles this entirely)
- Replacing case-queue (it is called via API; it remains a separate repo and service)
- Authentication or multi-user sessions (portfolio demo — no auth)
- WebSocket or SSE real-time push (polling is sufficient; 3s interval as per project 22)
- Data migration from moderation-stream's Postgres (fresh schema; moderation-stream is retired by this project)
- Kafka topic management UI or admin tooling
- Custom dbt scheduler (Makefile target is sufficient; no Airflow or Prefect)
- Any frontend work inside the case-queue repo (Human Review panel links to case-queue; no embedded iframe or cross-repo component)

---

## Assumptions

1. **Project location:** `projects/moderation-dashboard/` — new directory. Project 22 (`projects/moderation-stream/`) is archived but not deleted until moderation-dashboard is verified working.
2. **Starting point:** project 22 codebase is copied and refactored into moderation-dashboard. Not built from scratch.
3. **Consumer group naming:** production group = `moderation-production`; shadow groups = `moderation-shadow-distilbert`, `moderation-shadow-roberta`, `moderation-shadow-detoxify` (separate group per model for parallel coverage).
4. **Anomaly detection method:** rolling Z-score on 5-minute tumbling windows. No ML model for anomaly detection — statistical only. Simple, interpretable, no additional weight files.
5. **Escalation endpoint:** POST event content to `case-queue POST /cases` — the existing endpoint with a `source_system: "moderation-dashboard"` metadata field. Planner must verify case-queue's schema supports this; if not, a lightweight case-queue API extension may be required (single new field on CaseCreate schema).
6. **dbt adapter:** dbt-core + dbt-postgres. dbt project lives at `projects/moderation-dashboard/dbt/`. Models: `stg_events`, `stg_classifications`, `fct_category_trends`, `fct_model_accuracy`, `fct_escalation_rates`.
7. **Frontend:** new React/TypeScript app at `projects/moderation-dashboard/web/`. shadcn/ui + Tailwind (same pattern as case-queue). TanStack Query for data fetching, 3s polling for live panels.
8. **Postgres schema:** clean break from moderation-stream. New schema with tables for: raw events, classifications (production + shadow), anomaly flags, dbt-managed analytical tables.
9. **Phase 2 activation:** same pattern as project 22 — `MODEL_REGISTRY` in config drives active vs `pending_weights` state per consumer. Dashboard shows pending state for fine-tuned models until weights are wired.
10. **Case-queue escalation display:** Human Review panel polls `GET /cases?source_system=moderation-dashboard` on a 5s interval. Shows case count, links each case to case-queue detail view at its URL (not embedded). Graceful degradation if case-queue is unreachable.

---

## Handoff

**Next role:** planner

**What the planner does with this:**
- Define the complete file and module structure: which code is copied from project 22 as-is, which is refactored, which is new.
- Lock tech decisions: dbt model granularity, Kafka topic and partition config, Postgres schema design (tables, indexes, retention strategy for event volume).
- Specify the consumer group architecture in detail: how many partitions on the Kafka topic, how round-robin distribution actually works at the partition level, whether 3 consumers in one group with 3 partitions gives true round-robin.
- Define the anomaly detector interface: does it run as a separate consumer, a sidecar to the metrics API, or a scheduled job?
- Determine whether case-queue's schema needs extension for the escalation integration — flag if a case-queue API PR is needed before this project can complete.
- Define dbt model structure and identify which Postgres tables dbt reads from vs writes to.
- Confirm port allocation and Docker Compose layout.

**Flags for planner:**
- Assumption 5 (escalation endpoint) — planner must read `projects/case-queue/api/app/schemas.py` and `app/routers/cases.py` to confirm POST /cases schema. A `source_system` field may not exist; adding it to case-queue is a dependency that must be scoped and sequenced.
- Assumption 3 (consumer group round-robin) — Kafka round-robins across *partitions*, not consumers. If the topic has only 1 partition, all events go to one consumer. Planner must spec the partition count to match the number of production consumers (minimum 3 for Phase 1, 5 for Phase 2).
- Assumption 6 (dbt models) — planner should validate that the proposed dbt model names and grain are achievable given the Postgres schema design; adjust if needed.
- Memory budget on Hostinger — planner should estimate per-model memory footprint (DistilBERT ~260MB, RoBERTa ~480MB, Detoxify ~500MB) and confirm 3-model Phase 1 fits within 8GB alongside Kafka + Postgres + API + nginx.
