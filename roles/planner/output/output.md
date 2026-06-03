# Planner Output — moderation-dashboard

**Role:** planner
**Sequence:** `new-project-full` (step 2)
**Date:** 2026-06-03

---

## Project

`moderation-dashboard` — A unified content moderation platform that streams Jigsaw Toxic Comments through Kafka, routes events to N models via simultaneous round-robin production routing and parallel shadow evaluation, detects anomalies on the raw event stream, transforms results through dbt for rolling analytics, and escalates low-confidence cases to the case-queue service for human review.

---

## Requirements

### Streaming Infrastructure
1. A Kafka producer replays `resources/datasets/jigsaw-toxic-comments/train.csv` as a stream of `ModerationEvent` messages at a configurable rate (default 10 events/sec); supports SIGINT shutdown.
2. The Kafka topic (`moderation-events`) has **5 partitions** to support round-robin distribution across up to 5 Phase 2 consumers.

### Production Consumer Group (Round-Robin)
3. Three model consumers — DistilBERT zero-shot, RoBERTa zero-shot, Detoxify — run in consumer group `moderation-production`; Kafka distributes partitions across them.
4. Each production consumer records per-event results to Postgres: `event_id`, `model_name`, `group` (`production`), `predicted_label`, `confidence`, `latency_ms`, `correct` (vs Jigsaw ground truth), `created_at`.
5. `GET /metrics/production` returns per-model: `f1`, `precision`, `recall`, `latency_p50`, `latency_p95`, `throughput_per_sec`, `event_count`, `status` (`active` | `pending_weights`).

### Shadow Consumer Group (Parallel)
6. The same three model consumers each run in separate consumer groups (`moderation-shadow-distilbert`, `moderation-shadow-roberta`, `moderation-shadow-detoxify`); every event hits every shadow consumer.
7. Shadow results are recorded to the same `classifications` table with `group` = `shadow`.
8. `GET /metrics/shadow` returns per-model metrics (same shape as production).
9. `GET /metrics/comparison/{event_id}` returns all shadow verdicts for a specific event (all model predictions side-by-side).

### Anomaly Detection
10. An anomaly detector runs as a Kafka consumer in group `moderation-anomaly`; it processes every event in 5-minute tumbling windows tracking: event volume (Z-score), per-category classification rate (Z-score), shadow model disagreement rate.
11. When any signal's Z-score exceeds `ANOMALY_ZSCORE_THRESHOLD` (default 3.0), the window is written to the `anomaly_flags` table with: `window_start`, `signal_name`, `z_score`, `value`, `baseline_mean`, `baseline_std`.
12. `GET /metrics/anomalies` returns the 50 most recent anomaly flags ordered by `window_start` desc.
13. `GET /metrics/stream` returns: live event rate (events/sec derived from `classifications` timestamp density over last 60s), per-category event counts over last 5 minutes, total event count.

### Escalation
14. An escalation service runs as a standalone process; it polls shadow classification results and escalates events where: (a) shadow models disagree (not all models agree on binary label) OR (b) max softmax confidence across shadow models < `ESCALATION_CONFIDENCE_THRESHOLD` (default 0.6).
15. Escalated events are posted to case-queue `POST /cases` with `source="moderation-dashboard"` and `meta` containing `{"confidence_scores": {...}, "model_verdicts": {...}, "escalation_reason": "..."}`.
16. Each event is escalated at most once; dedup via an `escalations` table recording `event_id` and `escalated_at`.
17. The Human Review panel polls case-queue `GET /cases?source=moderation-dashboard&status=pending` on a 5s interval; shows count and list of pending escalated cases; each case links to `{VITE_CASE_QUEUE_URL}/cases/{id}`.
18. The Human Review panel renders a degraded state (error card, no crash) if case-queue is unreachable.
19. **Pre-condition:** case-queue `GET /cases` needs a `source` query param added (~10 lines to `projects/case-queue/api/app/routers/cases.py`). This is the first task of the implementer pass.

### dbt Analytics Layer
20. A dbt project at `dbt/` uses the `dbt-postgres` adapter; models materialise to a `dbt_moderation` schema in the same Postgres database (port 5434).
21. Staging models: `stg_events` (from `classifications` table filtered to unique event_ids), `stg_classifications` (from `classifications` table, both groups).
22. Mart models: `fct_category_trends` (hourly event counts by category), `fct_model_accuracy` (rolling 1-hour F1 per model per group), `fct_escalation_rates` (escalation count and rate per 5-minute window from `escalations` table).
23. `dbt build` and `dbt test` pass without errors against the live Postgres instance.
24. Schema tests in `dbt/models/schema.yml`: `not_null` and `unique` on primary keys; `accepted_values` on category and group columns.
25. `GET /metrics/analytics` queries the dbt mart tables directly and returns their results as JSON. No file I/O.
26. Makefile target `make dbt-refresh` runs `dbt build`.

### API
27. FastAPI metrics API on port 8002; `GET /health` returns `{"status": "ok"}` with HTTP 200.
28. CORS configured for frontend origin (`CORS_ORIGINS` env var, default `["http://localhost:5174"]`).
29. All aggregation endpoints (`/metrics/production`, `/metrics/shadow`, `/metrics/analytics`) include at least one integration test with seeded Postgres data asserting computed metric values — not just response shape.

### Frontend — 5 Panels
30. **Stream Monitor:** live event rate chart (events/sec, last 60s), per-category distribution bar chart, recent anomaly flags list. Polls `GET /metrics/stream` and `GET /metrics/anomalies` every 3s.
31. **Model Performance:** one card per model in the production group; displays F1, latency p50/p95, throughput; `pending_weights` cards shown greyed for Phase 2 models without checkpoints. Polls `GET /metrics/production` every 3s.
32. **Model Comparison:** shadow group accuracy delta table; clicking a model pair shows recent events where they disagreed (calls `GET /metrics/comparison/{event_id}`). Polls `GET /metrics/shadow` every 3s.
33. **Human Review:** escalation count badge, list of recent pending escalated cases from case-queue; each case links to `{VITE_CASE_QUEUE_URL}/cases/{id}`; degrades gracefully if case-queue unreachable. Polls every 5s.
34. **Analytics:** category trend chart (hourly, recharts LineChart), per-model accuracy chart (rolling), escalation rate chart. Polls `GET /metrics/analytics` every 60s.
35. All panels independently degrade: show skeleton/error state on fetch failure; sibling panels continue functioning.
36. Dev server runs on port 5174 (distinct from case-queue at 5173).

### Phase 2
37. Fine-tuned DistilBERT and RoBERTa consumers exist in both production and shadow groups; they activate when `DISTILBERT_CHECKPOINT_PATH` / `ROBERTA_CHECKPOINT_PATH` are set; they log and exit cleanly when paths are absent.
38. When Phase 2 consumers are active, all 5 model cards appear in Model Performance and Model Comparison panels.

### Testing
39. Producer: unit tests — event construction from CSV row, rate-limiting logic, topic creation.
40. Consumers: unit tests with mocked inference — result shape, `correct` field, latency > 0.
41. Anomaly detector: unit tests — Z-score computation with seeded windows (mean + 4σ triggers flag; mean ± 1σ does not).
42. Metrics API: integration tests with seeded Postgres — assert F1, latency p50, throughput, and anomaly flag retrieval against known seeded data.
43. dbt: `dbt test` passes all schema tests.
44. Frontend: vitest tests for each page component covering loading, error, and data-populated states.

### Operations
45. `docker-compose.yml` starts Kafka + Zookeeper + Postgres (port 5434).
46. Makefile targets: `make api`, `make producer`, `make consumers-production`, `make consumers-shadow`, `make anomaly-detector`, `make escalation-service`, `make dbt-refresh`, `make all`, `make stop`.
47. `.env.example` documents all required env vars with inline comments.
48. README covers prerequisites (Docker, uv, pnpm, librdkafka, dbt-core), local run, and Hostinger deploy guide.

---

## Technology Stack

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | Workspace standard |
| Package manager | uv | Workspace standard |
| Formatter/linter | ruff | Workspace standard |
| Web framework | FastAPI + uvicorn | Consistent with case-queue and project 22 |
| Kafka client | confluent-kafka | Same as project 22 |
| Model inference | transformers + torch (CPU) | Same as project 22; no CUDA dependency |
| Detoxify | detoxify | Same as project 22 |
| Metrics computation | scikit-learn | Same as project 22 |
| Anomaly detection | numpy (rolling Z-score) | No ML model; simple and interpretable |
| ORM | SQLAlchemy async + asyncpg | Consistent with case-queue and project 22 |
| Migrations | Alembic | Consistent; required before first deploy |
| Settings | pydantic-settings (`extra="ignore"`) | Consistent |
| HTTP client (escalation) | httpx async | Async-native |
| Analytics | dbt-core + dbt-postgres | Closes project 1 CV gap; no cloud tooling |
| Testing (Python) | pytest + pytest-asyncio | Workspace standard |
| Language (frontend) | TypeScript 5.x | Workspace standard |
| Package manager (frontend) | pnpm | Workspace standard |
| Build tool | Vite | Workspace standard |
| UI framework | React 18 | Workspace standard |
| Data fetching | TanStack Query | Consistent with case-queue |
| UI components | shadcn/ui + Tailwind CSS | Consistent with case-queue |
| Charts | recharts | Same as project 22 StreamDashboard |
| Testing (frontend) | vitest + @testing-library/react | Workspace standard |
| Infrastructure | Kafka + Zookeeper + PostgreSQL 16 (Docker) | Same as project 22 |

---

## File and Module Structure

```
projects/moderation-dashboard/
├── pyproject.toml              # uv project; entry points: producer, consumer, anomaly-detector, escalation-service, api
├── ruff.toml
├── Makefile
├── docker-compose.yml          # Kafka (9092) + Zookeeper + Postgres (5434)
├── .env.example
├── README.md
│
├── moderation_dashboard/
│   ├── __init__.py
│   ├── config.py               # Settings; MODEL_REGISTRY; escalation + anomaly thresholds
│   ├── types.py                # ModerationEvent, ClassificationResult Pydantic models
│   ├── producer.py             # load_jigsaw_csv, publish_events, ensure_topic, main
│   │
│   ├── consumers/
│   │   ├── __init__.py
│   │   ├── base.py             # BaseConsumer: poll loop, DB write, group_id constructor param
│   │   ├── distilbert.py       # DistilBertZeroShotConsumer
│   │   ├── roberta.py          # RobertaZeroShotConsumer
│   │   ├── detoxify_consumer.py
│   │   ├── finetuned.py        # FinetunedDistilBertConsumer, FinetunedRobertaConsumer
│   │   └── runner.py           # CLI: instantiates and runs a named consumer in a named group mode
│   │
│   ├── anomaly/
│   │   ├── __init__.py
│   │   └── detector.py         # Kafka consumer; 5-min tumbling windows; Z-score; DB write
│   │
│   ├── escalation/
│   │   ├── __init__.py
│   │   └── service.py          # polls shadow results; posts to case-queue; dedup via escalations table
│   │
│   └── api/
│       ├── __init__.py
│       ├── models.py           # ClassificationResult ORM, AnomalyFlag ORM, Escalation ORM
│       ├── schemas.py          # Pydantic response schemas
│       ├── database.py         # async engine, init_db, get_db
│       ├── main.py             # FastAPI app, lifespan, CORS, routers
│       └── routers/
│           ├── health.py
│           ├── stream.py       # GET /metrics/stream
│           ├── production.py   # GET /metrics/production
│           ├── shadow.py       # GET /metrics/shadow, GET /metrics/comparison/{event_id}
│           ├── anomalies.py    # GET /metrics/anomalies
│           └── analytics.py    # GET /metrics/analytics (queries dbt mart tables)
│
├── dbt/
│   ├── dbt_project.yml         # target schema: dbt_moderation
│   ├── profiles.yml            # postgres connection via env vars
│   └── models/
│       ├── schema.yml          # not_null, unique, accepted_values tests
│       ├── staging/
│       │   ├── stg_events.sql
│       │   └── stg_classifications.sql
│       └── marts/
│           ├── fct_category_trends.sql
│           ├── fct_model_accuracy.sql
│           └── fct_escalation_rates.sql
│
├── web/
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── vite.config.ts          # port 5174; @/ alias; vitest/config
│   ├── tsconfig.app.json       # strict; no baseUrl; paths @/*
│   ├── tailwind.config.js
│   ├── .env.example            # VITE_API_URL, VITE_CASE_QUEUE_URL
│   └── src/
│       ├── main.tsx
│       ├── App.tsx             # QueryClientProvider + Router + tab nav
│       ├── types/
│       │   ├── index.ts        # ModerationEvent, ClassificationResult, AnomalyFlag
│       │   └── analytics.ts    # dbt output response types
│       ├── api/
│       │   ├── client.ts       # apiFetch, ApiError
│       │   ├── stream.ts       # useStreamMetrics
│       │   ├── production.ts   # useProductionMetrics
│       │   ├── shadow.ts       # useShadowMetrics, useEventComparison
│       │   ├── anomalies.ts    # useAnomalies
│       │   ├── analytics.ts    # useAnalytics
│       │   └── escalations.ts  # useEscalations (polls case-queue API)
│       ├── components/
│       │   ├── ModelCard.tsx   # active and pending_weights states
│       │   ├── MetricChart.tsx # recharts sparkline wrapper
│       │   ├── AnomalyBadge.tsx
│       │   └── ErrorMessage.tsx
│       ├── pages/
│       │   ├── StreamMonitor.tsx
│       │   ├── ModelPerformance.tsx
│       │   ├── ModelComparison.tsx
│       │   ├── HumanReview.tsx
│       │   └── Analytics.tsx
│       └── test/
│           ├── setup.ts
│           ├── StreamMonitor.test.tsx
│           ├── ModelPerformance.test.tsx
│           ├── ModelComparison.test.tsx
│           ├── HumanReview.test.tsx
│           └── Analytics.test.tsx
│
└── tests/
    ├── conftest.py
    ├── test_producer.py
    ├── test_consumers.py
    ├── test_anomaly.py
    └── test_api.py
```

---

## Pre-Condition: Case-Queue Source Filter PR

Before the Human Review panel can show live data, `projects/case-queue/api/app/routers/cases.py` needs a `source` query parameter on `GET /cases` (~10 lines). The `source` column already exists on the `Case` model and is stored. This is the first task of the implementer pass — done before any moderation-dashboard code.

---

## Open Questions for Architect

**Q1 — Consumer runner process model**
How does each consumer run in production?
- **Proposed answer:** Each consumer is a separate OS process. `runner.py` is a thin CLI that instantiates and runs one named consumer in one named group mode (`production` | `shadow`). Makefile launches all processes. No threading.

**Q2 — Anomaly detector process model**
Kafka consumer (real-time) or Postgres poller (scheduled)?
- **Proposed answer:** Kafka consumer in group `moderation-anomaly`. Real-time, sub-second detection latency. Reads same topic as model consumers; its own consumer group gets all events.

**Q3 — Escalation service process model**
Standalone process or background asyncio task in API?
- **Proposed answer:** Standalone process (`uv run escalation-service`). Independent lifecycle; restart without bouncing the API.

**Q4 — Raw events table**
Does the producer write raw events to Postgres?
- **Proposed answer:** No. Producer writes to Kafka only. `GET /metrics/stream` derives event rate from `classifications` table timestamp density. The anomaly detector (Kafka consumer) has its own view of the raw stream. No `raw_events` table needed.

**Q5 — Single `classifications` table vs two tables**
- **Proposed answer:** Single `classifications` table with a `group` column (`production` | `shadow`). Index on `(group, model_name, created_at)`. Sufficient for demo scale.

**Q6 — dbt schema permissions**
- **Proposed answer:** dbt materialises to `dbt_moderation` schema; `CREATE SCHEMA IF NOT EXISTS dbt_moderation` runs in dbt on first `dbt build`. The API Postgres user needs `SELECT` on `dbt_moderation.*`. Architect should spec the user grants in the deploy guide.

---

## Handoff

**Next role:** architect

**What the architect does with this:**
- Design the full Postgres schema: `classifications` table (all columns, indexes), `anomaly_flags` table, `escalations` table.
- Design `BaseConsumer` constructor and poll loop interface — how `group_id` is passed and used.
- Design `RollingWindowDetector`: window state (in-memory dict keyed by window boundary), Z-score computation, write path.
- Design the escalation service: polling query, dedup check, httpx call structure, retry behaviour.
- Design all API response schemas with concrete field names and types.
- Design the 5 dbt SQL models (grain, joins, aggregation logic).
- Confirm or override proposed answers to Q1–Q6.
- Specify `MODEL_REGISTRY` config structure (adapting from project 22 pattern: model key → consumer class + checkpoint path env var + status).

**Flags for architect:**
- Q1 (process model) directly affects runner.py design and Makefile — lock first.
- Q4 (raw events table) determines whether `GET /metrics/stream` is a simple timestamp query or needs additional storage.
- The case-queue source filter PR is a known 10-line dependency — architect should note it in the implementation sequence but it does not block any architectural decisions.
