# Planner Output — moderation-stream

**Role:** planner
**Sequence:** `new-project-full` (step 2)
**Date:** 2026-06-02

---

## Project

`moderation-stream` — Kafka-based content moderation event streaming platform with a five-model live comparison pipeline. A Python producer replays the Jigsaw Toxic Comment dataset as a configurable-speed Kafka stream; five classifier consumers run in parallel against each event; a FastAPI metrics service aggregates per-model accuracy, latency, and throughput to Postgres; a React `/stream` route added to the case-queue frontend shows the live comparison panel.

---

## Requirements

### Producer

1. The producer reads the Jigsaw Toxic Comment dataset from a local CSV path (configured via `JIGSAW_CSV_PATH` env var) and publishes each row as a JSON message to the Kafka topic `moderation-events`.
2. Each message contains: `event_id` (UUID v4), `text` (string), `label` (int 0/1, ground-truth toxic/not-toxic), `label_detail` (dict of per-category Jigsaw scores: `toxic`, `severe_toxic`, `obscene`, `threat`, `insult`, `identity_hate`).
3. The producer publishes at a configurable rate (`PRODUCER_RATE_PER_SEC`, default 10, max 100). It sleeps between batches to honour the rate.
4. The producer accepts `--limit N` to cap total messages for dev runs (default: 1 000; full dataset: 159 571 rows).
5. The producer exits cleanly on `SIGINT`; it prints total messages published and elapsed time on exit.

### Consumers

6. Each classifier runs as an independent OS process with its own Kafka consumer group ID (e.g. `consumer-distilbert`, `consumer-roberta`, `consumer-detoxify`).
7. Each consumer classifies the message text, records `predicted_label` (int 0/1), and records `latency_ms` (float — time from message receipt to classification complete).
8. Each consumer writes one `ClassificationResult` row to Postgres per message: `event_id`, `model_name`, `predicted_label`, `latency_ms`, `correct` (bool, `predicted_label == label`), `processed_at` (timestamp).
9. Phase 2 consumers (fine-tuned DistilBERT, fine-tuned RoBERTa) read checkpoint paths from `DISTILBERT_CHECKPOINT_PATH` and `ROBERTA_CHECKPOINT_PATH`. If the env var is unset or path does not exist, the consumer starts, logs a warning, and emits `status: pending_weights` in the metrics API rather than processing events.
10. Consumer groups commit offsets after each batch; on restart, each consumer resumes from the last committed offset.

### Metrics API

11. `GET /metrics` returns an array of per-model objects: `model_name`, `status` (`active` or `pending_weights`), `total_processed`, `correct`, `accuracy` (float 0–1), `p50_latency_ms`, `p95_latency_ms`, `throughput_cps` (classifications per second over the last 60 seconds).
12. `GET /health` returns `{"status": "ok"}`.
13. The metrics API reads `classification_results` from Postgres and computes all aggregates on query. No pre-aggregation table in Phase 1.
14. The metrics API connects to a separate database (`moderation_stream_db`) on the same Postgres instance as case-queue.
15. The metrics API exposes CORS allowing the case-queue frontend origin (`http://localhost:5173` in dev, configurable via `ALLOWED_ORIGIN` env var).

### Frontend — `/stream` route

16. A new `/stream` route is added to `projects/case-queue/web/src/App.tsx`.
17. The route renders five `ModelMetricsCard` components — one per model slot — in a responsive grid.
18. Each card shows: model name, status badge (`Active` / `Pending Weights`), accuracy (%), p50 / p95 latency (ms), throughput (cases/sec), total processed count.
19. The route polls `GET /metrics` every 3 seconds using TanStack Query `useQuery` with `refetchInterval`.
20. A nav link to `/stream` is added to the case-queue top navigation.
21. When the metrics API is unreachable, the dashboard renders an error state using the existing `ErrorMessage` component.

### Infrastructure

22. `docker compose up` in `projects/moderation-stream/` starts: Kafka (single broker), Zookeeper, and a Postgres instance (`moderation_stream_db` database). The case-queue `docker-compose.yml` is unchanged.
23. A `Makefile` provides: `make producer`, `make consumers` (starts all 3 Phase 1 consumers in background), `make api`, `make all`.
24. The producer creates the `moderation-events` topic on startup if it does not exist (no manual topic creation step).
25. All five consumer processes (Phase 1 + Phase 2 slots) are listed in the Makefile; Phase 2 targets are present but result in `pending_weights` mode until checkpoint env vars are set.

---

## Technology Stack

### Python (moderation-stream backend)

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | Workspace standard |
| Package manager | uv | Workspace standard |
| Formatter / linter | ruff | Workspace standard |
| Kafka client | `confluent-kafka-python` | Production-grade; lower latency than `kafka-python`. Requires `librdkafka` (macOS: `brew install librdkafka`; Linux: `apt install librdkafka-dev`) — documented in README. |
| Transformer inference | `transformers` + `torch` (CPU) | Standard HuggingFace interface; `device=-1` forces CPU; no GPU dependency |
| Detoxify | `detoxify` | Wraps `unitary/toxic-bert`; single-call toxicity classification |
| Metrics API | `fastapi` + `uvicorn` | Matches case-queue stack |
| ORM (API only) | `sqlalchemy[asyncio]` + `asyncpg` | Async reads in FastAPI; matches case-queue pattern |
| ORM (consumers) | `sqlalchemy` (sync) + `psycopg2` | Consumers run a blocking Kafka poll loop; sync DB writes are simpler and sufficient |
| Config | `pydantic-settings` | `extra="ignore"` per python-conventions.md |
| Validation | `pydantic` v2 | Shared event schemas between producer and consumers |
| Testing | `pytest` + `pytest-asyncio` | Workspace standard |

### TypeScript (case-queue frontend extension)

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | TypeScript 5.x strict | Existing frontend; workspace standard |
| Polling | TanStack Query `refetchInterval` | Already installed; correct tool for polling |
| UI components | shadcn/ui (existing) | Already installed; no new library |
| Testing | vitest + `@testing-library/react` | Existing case-queue setup |

---

## File and Module Structure

### Python project — `projects/moderation-stream/`

```
moderation-stream/
├── pyproject.toml                     # uv project; hatchling build; pytest asyncio_mode=auto
├── ruff.toml                          # line-length=100, select E/F/I/UP/B
├── docker-compose.yml                 # Kafka + Zookeeper + Postgres (moderation_stream_db)
├── .env.example                       # JIGSAW_CSV_PATH, KAFKA_BOOTSTRAP, DATABASE_URL, PRODUCER_RATE_PER_SEC
├── Makefile                           # producer / consumers / api / all targets
├── moderation_stream/
│   ├── __init__.py
│   ├── config.py                      # pydantic-settings Settings; extra="ignore"
│   ├── types.py                       # Pydantic models: ModerationEvent, ClassificationResult, ModelMetrics
│   ├── producer.py                    # Kafka producer; reads Jigsaw CSV; CLI entry point
│   ├── consumers/
│   │   ├── __init__.py
│   │   ├── base.py                    # BaseConsumer: Kafka poll loop, DB write, latency measurement
│   │   ├── distilbert.py              # zero-shot DistilBERT consumer (Phase 1)
│   │   ├── roberta.py                 # zero-shot RoBERTa consumer (Phase 1)
│   │   ├── detoxify_consumer.py       # Detoxify consumer (Phase 1)
│   │   └── finetuned.py               # Phase 2: loads checkpoint from env var; pending_weights if absent
│   └── api/
│       ├── __init__.py
│       ├── main.py                    # FastAPI app; lifespan; CORS
│       ├── database.py                # async engine + session factory; init_db()
│       ├── models.py                  # SQLAlchemy ORM: ClassificationResult table
│       ├── schemas.py                 # Pydantic response schemas: ModelMetrics, MetricsResponse
│       └── routers/
│           └── metrics.py             # GET /metrics, GET /health
└── tests/
    ├── conftest.py                    # test DB; mock Kafka fixtures
    ├── test_producer.py               # message shape, rate limiting, --limit flag
    ├── test_consumers.py              # classification result shape; pending_weights mode
    └── test_api.py                    # GET /metrics accuracy calculations; GET /health
```

**CLI entry points** (in `pyproject.toml` `[project.scripts]`):
- `moderation-stream-producer` → `moderation_stream.producer:main`
- `moderation-stream-distilbert` → `moderation_stream.consumers.distilbert:main`
- `moderation-stream-roberta` → `moderation_stream.consumers.roberta:main`
- `moderation-stream-detoxify` → `moderation_stream.consumers.detoxify_consumer:main`
- `moderation-stream-finetuned-distilbert` → `moderation_stream.consumers.finetuned:main_distilbert`
- `moderation-stream-finetuned-roberta` → `moderation_stream.consumers.finetuned:main_roberta`
- `moderation-stream-api` → `moderation_stream.api.main:run`

### Frontend additions — `projects/case-queue/web/src/`

```
src/
├── api/
│   └── stream.ts               # NEW: useStreamMetrics() TanStack Query hook
├── types/
│   └── stream.ts               # NEW: ModelMetrics type; StreamMetricsResponse type
├── pages/
│   └── StreamDashboard.tsx     # NEW: /stream route; 5-card grid; polling; error state
├── components/
│   └── ModelMetricsCard.tsx    # NEW: single model card — name, status badge, all metrics
└── App.tsx                     # MODIFIED: add /stream route + nav link
```

---

## Resolved Brief Flags

| Flag | Decision | Reason |
|------|----------|--------|
| Metrics store: in-memory vs Postgres | **Postgres** | Survives consumer restarts; consistent with existing stack; portfolio signal |
| Kafka client: confluent vs kafka-python | **confluent-kafka-python** | Production-grade; one-time `librdkafka` install is documented |
| Phase 2 slot activation | **Env var** (`DISTILBERT_CHECKPOINT_PATH`, `ROBERTA_CHECKPOINT_PATH`) | Config change only; no code change to enable Phase 2 |

---

## Open Questions for Architect

1. **Consumer DB write pattern.** Each consumer runs a blocking Kafka poll loop (no asyncio). Sync SQLAlchemy with psycopg2 is proposed — confirm this is the right call vs running asyncio inside each consumer process. This affects every consumer file and `BaseConsumer`.

2. **Metrics query performance.** `GET /metrics` computes accuracy, p50/p95, and throughput live from `classification_results` on each request. At full dataset completion: ~800K rows (159 571 × 5 models). Architect should decide: (a) index on `(model_name, processed_at)` only, or (b) add a pre-aggregation step. Phase 1 can start without pre-aggregation; architect should note the row threshold where it becomes necessary.

3. **`BaseConsumer` structure.** Architect should define the abstract interface: what `BaseConsumer.__init__` accepts, what `classify(text: str) -> tuple[int, float]` must return, and how the poll-classify-write loop is structured so each subclass only overrides `classify`.

---

## Handoff

**Next role:** architect
**What the architect does with this output:**
- Design `ModerationEvent`, `ClassificationResult`, `ModelMetrics` Pydantic schemas and SQLAlchemy ORM models.
- Define `BaseConsumer` abstract interface: poll loop, classify hook, DB write, offset commit.
- Design `GET /metrics` SQL query and confirm indexing strategy (open question 2).
- Define Kafka topic config and producer message serialisation.
- Define React component interfaces: `ModelMetricsCard` props, `useStreamMetrics` return type.
- Resolve all three open questions with explicit code patterns, not just decisions.

**Flags for architect:**
- Open question 1 (sync DB in consumers) is the most structurally significant — it affects `BaseConsumer` and every subclass.
- Open question 2 (query scale) should be resolved before implementer writes the metrics router.
- The dual ORM pattern (sync in consumers, async in API) must be clearly documented so the implementer does not accidentally mix them.
