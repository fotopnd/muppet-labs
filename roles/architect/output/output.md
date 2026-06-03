# Architect Output — moderation-dashboard

**Role:** architect
**Sequence:** `new-project-full` (step 3)
**Date:** 2026-06-03

---

## Open Question Resolutions

All six planner questions resolved as proposed — no overrides needed:
- **Q1** Consumer process model: one OS process per consumer, `runner.py` as thin CLI ✓
- **Q2** Anomaly detector: Kafka consumer in group `moderation-anomaly` ✓
- **Q3** Escalation service: standalone process ✓
- **Q4** No `raw_events` table; `GET /metrics/stream` derives event rate from `classifications` timestamp density ✓
- **Q5** Single `classifications` table with `group` column ✓
- **Q6** dbt materialises to `dbt_moderation` schema; API queries mart tables directly ✓

---

## System Overview

Nine independent processes share a single Postgres database and a single Kafka topic (`moderation-events`, 5 partitions). The **producer** reads the Jigsaw CSV and publishes `ModerationEvent` messages. Six **consumer processes** subscribe: three in group `moderation-production` (Kafka round-robins partitions across them) and three in separate shadow groups (each gets all partitions, all events). Each consumer writes a `ClassificationResult` row to `classifications`. An **anomaly detector** runs in its own group `moderation-anomaly`, maintains 5-minute tumbling windows of volume and category signals from the raw event stream, and queries Postgres at flush time for shadow disagreement rate; it writes `AnomalyFlag` rows when Z-score thresholds trigger. A standalone **escalation service** polls shadow classifications, identifies uncertain events by disagreement or low confidence, and POSTs them to the case-queue API; it writes an `Escalation` row per event for dedup. The **FastAPI metrics API** runs async, queries Postgres and the dbt mart tables, and serves all dashboard panels. A **dbt CLI** (run on demand via `make dbt-refresh`) materialises staging and mart models into the `dbt_moderation` schema. The **React frontend** polls the metrics API (3–60s intervals) and polls case-queue directly for the Human Review panel.

---

## Data Models

### Postgres Tables

**`classifications`** — written by all 6 consumer processes (sync)
```
id:               TEXT PRIMARY KEY         -- uuid4
event_id:         TEXT NOT NULL            -- producer-assigned uuid per CSV row
group:            TEXT NOT NULL            -- 'production' | 'shadow'
model_name:       TEXT NOT NULL            -- 'distilbert' | 'roberta' | 'detoxify' | 'finetuned_distilbert' | 'finetuned_roberta'
category:         TEXT NOT NULL            -- primary Jigsaw category forwarded from event
predicted_label:  INTEGER NOT NULL         -- 0 | 1
confidence:       DOUBLE PRECISION NOT NULL
latency_ms:       DOUBLE PRECISION NOT NULL
correct:          BOOLEAN NOT NULL         -- predicted_label == ground_truth
created_at:       TIMESTAMPTZ NOT NULL

Indexes:
  ix_classifications_group_model_created  ON (group, model_name, created_at)
  ix_classifications_event_group          ON (event_id, group)
  ix_classifications_created_at           ON (created_at)
```

**`anomaly_flags`** — written by anomaly detector (sync)
```
id:               TEXT PRIMARY KEY         -- uuid4
window_start:     TIMESTAMPTZ NOT NULL
window_end:       TIMESTAMPTZ NOT NULL
signal_name:      TEXT NOT NULL            -- 'event_volume' | 'category_rate_{cat}' | 'disagreement_rate'
z_score:          DOUBLE PRECISION NOT NULL
value:            DOUBLE PRECISION NOT NULL -- observed value in window
baseline_mean:    DOUBLE PRECISION NOT NULL
baseline_std:     DOUBLE PRECISION NOT NULL
created_at:       TIMESTAMPTZ NOT NULL

Index:
  ix_anomaly_flags_window_start  ON (window_start DESC)
```

**`escalations`** — written by escalation service (sync)
```
id:                   TEXT PRIMARY KEY     -- uuid4
event_id:             TEXT NOT NULL UNIQUE -- dedup key
case_queue_case_id:   TEXT NOT NULL        -- ID returned from case-queue POST /cases
escalation_reason:    TEXT NOT NULL        -- 'model_disagreement' | 'low_confidence'
confidence_max:       DOUBLE PRECISION     -- nullable; null when reason = 'model_disagreement'
created_at:           TIMESTAMPTZ NOT NULL

Index:
  ix_escalations_event_id    ON (event_id)   -- UNIQUE; dedup lookup
  ix_escalations_created_at  ON (created_at DESC)
```

### Kafka Message Schema

**`ModerationEvent`** — Pydantic model, serialised as JSON to Kafka
```python
class ModerationEvent(BaseModel):
    event_id: str        # uuid4 assigned by producer
    jigsaw_id: int       # CSV row index (0-based)
    content: str         # comment_text column
    ground_truth: int    # 0 | 1 — Jigsaw 'toxic' column
    category: str        # primary category — see producer.get_primary_category()
    published_at: datetime
```

Category priority (producer): `severe_toxic > threat > identity_hate > obscene > insult > toxic > clean`

**`ClassificationResult`** — internal type (not serialised to Kafka)
```python
class ClassificationResult(BaseModel):
    event_id: str
    model_name: str
    group: str
    category: str        # forwarded from ModerationEvent
    predicted_label: int
    confidence: float
    latency_ms: float
    correct: bool        # predicted_label == event.ground_truth
    created_at: datetime
```

### dbt Source + Models

**Source:** `moderation` schema — tables `classifications`, `escalations`

**Staging:**
- `stg_events` — distinct events: `SELECT DISTINCT ON (event_id) event_id, ground_truth, category, date_trunc('hour', created_at) AS event_hour, created_at FROM classifications ORDER BY event_id, created_at`
- `stg_classifications` — cleaned classifications with `date_trunc('hour', created_at) AS classification_hour`

**Marts:**
- `fct_category_trends` — grain: `(event_hour, category)`; columns: `event_count`; source: `stg_events`
- `fct_model_accuracy` — grain: `(classification_hour, group, model_name)`; columns: `n, tp, fp, fn, f1`; F1 = `2*tp / (2*tp + fp + fn)`; TP/FP/FN derived from `predicted_label` + `correct`
- `fct_escalation_rates` — grain: `(window_5min)`; columns: `escalation_count, total_events, escalation_rate`; joins `stg_events` windowed counts with `escalations` windowed counts

All marts materialised as `table` (not `view`) so API queries hit pre-computed rows.

### Config & Registry

```python
@dataclass
class ModelSpec:
    model_key: str
    display_name: str
    requires_checkpoint: bool
    checkpoint_path_env_var: str | None  # None for zero-shot models

MODEL_REGISTRY: dict[str, ModelSpec] = {
    "distilbert":          ModelSpec("distilbert",          "DistilBERT (zero-shot)",    False, None),
    "roberta":             ModelSpec("roberta",             "RoBERTa (zero-shot)",       False, None),
    "detoxify":            ModelSpec("detoxify",            "Detoxify",                  False, None),
    "finetuned_distilbert": ModelSpec("finetuned_distilbert", "DistilBERT (fine-tuned)", True, "DISTILBERT_CHECKPOINT_PATH"),
    "finetuned_roberta":   ModelSpec("finetuned_roberta",   "RoBERTa (fine-tuned)",      True, "ROBERTA_CHECKPOINT_PATH"),
}
```

---

## Module Interfaces

### `config.py`

```python
class Settings(BaseSettings):
    model_config = ConfigDict(extra="ignore")

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "moderation-events"
    kafka_num_partitions: int = 5

    # Postgres — two URLs for sync (consumers) and async (API)
    postgres_url_sync: str       # postgresql+psycopg2://postgres:postgres@localhost:5434/moderation_dashboard
    postgres_url_async: str      # postgresql+asyncpg://postgres:postgres@localhost:5434/moderation_dashboard

    # Producer
    jigsaw_csv_path: Path
    producer_rate_per_sec: float = 10.0

    # Phase 2 checkpoints (None = pending_weights)
    distilbert_checkpoint_path: Path | None = None
    roberta_checkpoint_path: Path | None = None

    # Escalation
    escalation_confidence_threshold: float = 0.6
    escalation_poll_interval_secs: float = 10.0
    case_queue_api_url: str = "http://localhost:8000"

    # Anomaly detection
    anomaly_zscore_threshold: float = 3.0
    anomaly_window_minutes: int = 5
    anomaly_min_history_windows: int = 10  # skip checks until N windows of baseline

    # API
    cors_origins: list[str] = ["http://localhost:5174"]

    # dbt
    dbt_project_dir: Path  # absolute path to dbt/ directory

@lru_cache
def get_settings() -> Settings: ...
```

### `producer.py`

```python
CATEGORY_PRIORITY: list[str] = ["severe_toxic", "threat", "identity_hate", "obscene", "insult", "toxic"]

def load_jigsaw_csv(path: Path) -> list[dict[str, Any]]: ...

def get_primary_category(row: dict[str, Any]) -> str:
    # Returns first positive label in CATEGORY_PRIORITY, or "clean"
    ...

def ensure_topic(bootstrap_servers: str, topic: str, num_partitions: int) -> None:
    # AdminClient.create_topics(); no-op if topic already exists
    ...

def publish_events(
    events: list[dict[str, Any]],
    bootstrap_servers: str,
    topic: str,
    rate_per_sec: float,
) -> None:
    # Publishes ModerationEvent JSON; rate-limits with time.sleep; SIGINT exits cleanly
    ...

def main() -> None: ...   # CLI entry point; reads Settings; calls ensure_topic then publish_events
```

### `consumers/base.py`

```python
class BaseConsumer:
    model_name: str
    group_id: str

    def __init__(
        self,
        model_name: str,
        group_id: str,       # 'moderation-production' | 'moderation-shadow-{model_name}'
        bootstrap_servers: str,
        topic: str,
        db_url: str,         # sync postgres URL (postgresql+psycopg2://...)
    ) -> None: ...

    def classify(self, content: str) -> tuple[int, float]:
        # Returns (predicted_label: 0|1, confidence: 0.0–1.0)
        # Subclasses override; raises RuntimeError if weights not loaded
        raise NotImplementedError

    def run(self) -> None:
        # Sync poll loop; SIGINT exits cleanly
        # Per message:
        #   1. Parse ModerationEvent from JSON
        #   2. t0 = time.perf_counter(); label, conf = self.classify(event.content); latency_ms = (perf_counter()-t0)*1000
        #   3. correct = (label == event.ground_truth)
        #   4. _write_result(ClassificationResult(...))
        ...

    def _write_result(self, result: ClassificationResult) -> None:
        # Sync SQLAlchemy session; INSERT INTO classifications
        ...
```

### `consumers/runner.py`

CLI: `uv run consumer --model <model_key> --mode <production|shadow>`

```python
def main() -> None:
    # 1. Parse --model and --mode args (argparse or typer)
    # 2. Look up ModelSpec in MODEL_REGISTRY
    # 3. If requires_checkpoint: check env var; if unset, log warning and sys.exit(0)
    # 4. Construct group_id:
    #      production → "moderation-production"
    #      shadow     → f"moderation-shadow-{model_key}"
    # 5. Instantiate consumer class; call consumer.run()
```

### `anomaly/detector.py`

```python
@dataclass
class WindowState:
    window_start: datetime
    window_end: datetime
    event_count: int
    category_counts: dict[str, int]   # category → count
    # disagreement_rate computed at flush from Postgres query (not tracked in-memory)

class RollingWindowDetector:
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        db_url: str,         # sync postgres URL
        window_minutes: int = 5,
        zscore_threshold: float = 3.0,
        min_history: int = 10,
    ) -> None: ...

    def run(self) -> None:
        # Kafka consumer group: 'moderation-anomaly'
        # Poll loop; on each event:
        #   1. Determine window boundary for event.published_at
        #   2. If event is in a new window, call _flush_window() on completed window
        #   3. Update current window state
        ...

    def _flush_window(self, state: WindowState) -> None:
        # 1. Append window volume to history; compute Z-score vs history
        # 2. Append per-category rates to history; compute Z-scores
        # 3. Query Postgres for shadow disagreement rate in window time range
        # 4. Append disagreement rate to history; compute Z-score
        # 5. For any signal where |z_score| > threshold and len(history) >= min_history:
        #      write AnomalyFlag row
        ...

    def _compute_zscore(self, value: float, history: list[float]) -> float:
        # numpy: (value - np.mean(history)) / np.std(history)
        # Returns 0.0 if len(history) < 2
        ...

    def _get_shadow_disagreement_rate(
        self, window_start: datetime, window_end: datetime
    ) -> float:
        # Query: for each event in window with >= 2 shadow classifications,
        #        disagreement = not all models agree on predicted_label
        # Returns: count(disagreeing events) / count(events with >= 2 shadow classifications)
        ...
```

### `escalation/service.py`

```python
class EscalationService:
    def __init__(
        self,
        db_url: str,
        case_queue_api_url: str,
        confidence_threshold: float = 0.6,
        poll_interval_secs: float = 10.0,
    ) -> None: ...

    def run(self) -> None:
        # Loop with SIGINT shutdown; sleep poll_interval_secs between cycles
        ...

    def _get_unevaluated_event_ids(self) -> list[str]:
        # SELECT DISTINCT c.event_id
        # FROM classifications c
        # LEFT JOIN escalations e ON c.event_id = e.event_id
        # WHERE c.group = 'shadow'
        #   AND e.event_id IS NULL
        # GROUP BY c.event_id
        # HAVING COUNT(DISTINCT c.model_name) >= 2
        ...

    def _evaluate_event(
        self, event_id: str, shadow_rows: list[Row]
    ) -> tuple[bool, str, float | None]:
        # Returns (should_escalate, reason, confidence_max)
        # Disagreement: set(predicted_label) has more than one unique value
        # Low confidence: max(confidence) < threshold
        ...

    def _get_event_content(self, event_id: str) -> tuple[str, str]:
        # SELECT content (from Kafka event — not stored in DB)
        # Problem: content is not in the classifications table
        # Resolution: see Implementation Notes — content must be in classifications table
        ...

    def _post_to_case_queue(
        self,
        content: str,
        category: str,
        reason: str,
        confidence_max: float | None,
        shadow_rows: list[Row],
    ) -> str:
        # httpx.Client().post(f"{case_queue_api_url}/cases", json={...})
        # Returns case_queue_case_id
        # Raises on HTTP error; caller catches and logs
        ...

    def _write_escalation(
        self, event_id: str, case_queue_case_id: str, reason: str, confidence_max: float | None
    ) -> None: ...
```

**Critical note on event content:** The event's `content` (text) and `category` must be stored in `classifications` so the escalation service can retrieve them without a separate lookup. Add `content: TEXT NOT NULL` and the schema already has `category`. This avoids requiring a raw_events table while giving the escalation service what it needs to POST a meaningful case to case-queue.

**Updated `classifications` table** (add one column):
```
content: TEXT NOT NULL   -- ADD THIS; forwarded from ModerationEvent.content
```

### `api/models.py`

```python
class Classification(Base):
    __tablename__ = "classifications"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(String, nullable=False)
    group: Mapped[str] = mapped_column(String, nullable=False)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    predicted_label: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Double, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Double, nullable=False)
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class AnomalyFlag(Base):
    __tablename__ = "anomaly_flags"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    signal_name: Mapped[str] = mapped_column(String, nullable=False)
    z_score: Mapped[float] = mapped_column(Double, nullable=False)
    value: Mapped[float] = mapped_column(Double, nullable=False)
    baseline_mean: Mapped[float] = mapped_column(Double, nullable=False)
    baseline_std: Mapped[float] = mapped_column(Double, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class Escalation(Base):
    __tablename__ = "escalations"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    case_queue_case_id: Mapped[str] = mapped_column(String, nullable=False)
    escalation_reason: Mapped[str] = mapped_column(String, nullable=False)
    confidence_max: Mapped[float | None] = mapped_column(Double, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

### `api/schemas.py`

```python
class ModelStatus(StrEnum):
    active = "active"
    pending_weights = "pending_weights"

class ModelMetrics(BaseModel):
    model_name: str
    display_name: str
    status: ModelStatus
    event_count: int
    f1: float | None
    precision: float | None
    recall: float | None
    latency_p50: float | None
    latency_p95: float | None
    throughput_per_sec: float | None

class EventComparison(BaseModel):
    event_id: str
    content: str
    category: str
    ground_truth: int
    classifications: list[SingleModelVerdict]

class SingleModelVerdict(BaseModel):
    model_name: str
    predicted_label: int
    confidence: float
    latency_ms: float
    correct: bool

class AnomalyFlagRead(BaseModel):
    id: str
    window_start: datetime
    window_end: datetime
    signal_name: str
    z_score: float
    value: float
    baseline_mean: float
    baseline_std: float
    created_at: datetime

class StreamMetrics(BaseModel):
    event_rate_per_sec: float     # unique events in last 60s / 60
    category_counts: dict[str, int]  # last 5 min
    total_events: int

class AnalyticsResponse(BaseModel):
    category_trends: list[CategoryTrend]
    model_accuracy: list[ModelAccuracyPoint]
    escalation_rates: list[EscalationRatePoint]

class CategoryTrend(BaseModel):
    hour: datetime
    category: str
    event_count: int

class ModelAccuracyPoint(BaseModel):
    hour: datetime
    group: str
    model_name: str
    f1: float
    n: int

class EscalationRatePoint(BaseModel):
    window_start: datetime
    escalation_count: int
    total_events: int
    escalation_rate: float
```

### API Route Contracts

```
GET  /health
     → 200 {"status": "ok"}

GET  /metrics/stream
     → StreamMetrics

GET  /metrics/production
     → list[ModelMetrics]
     (includes pending_weights entries for all 5 MODEL_REGISTRY keys)

GET  /metrics/shadow
     → list[ModelMetrics]

GET  /metrics/comparison/{event_id}
     → EventComparison | 404

GET  /metrics/anomalies
     → list[AnomalyFlagRead]   (limit 50, ordered by window_start DESC)

GET  /metrics/analytics
     → AnalyticsResponse
     (queries dbt_moderation.fct_* tables; returns empty lists if dbt not yet run)
```

---

## Dependencies

```
producer.py           → config.py, types.py
consumers/base.py     → config.py, types.py, api/models.py (sync session)
consumers/*.py        → consumers/base.py
consumers/runner.py   → consumers/*.py, config.py
anomaly/detector.py   → config.py, types.py, api/models.py (sync session)
escalation/service.py → config.py, types.py, api/models.py (sync session)
api/models.py         → (standalone — no moderation_dashboard imports)
api/schemas.py        → config.py (ModelStatus, MODEL_REGISTRY)
api/database.py       → config.py
api/routers/*.py      → api/models.py, api/schemas.py, api/database.py
api/main.py           → api/routers/*, api/database.py, config.py
```

No circular dependencies. `api/models.py` is the sole shared ORM layer; sync processes import it via a sync engine, the API imports it via an async engine. The ORM class definitions are the same — only the engine/session differ.

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Error handling (sync) | Consumer/detector/escalation poll loops: catch `Exception`, log `exc_info=True`, continue. Never crash on a single bad message. |
| Error handling (API) | Let FastAPI handle exceptions. `HTTPException` for 4xx. Unhandled exceptions → 500. |
| Uninitialised state | Fine-tuned consumers that can't load weights must `raise RuntimeError` — not return a silent default. |
| Logging | `logging.getLogger(__name__)` in every module. Root logger configured in each process entry point. Level `INFO` default; consumer classification loop at `DEBUG`. |
| Configuration | `get_settings()` with `@lru_cache`. Single `.env` file; `extra="ignore"` on all settings models. Both `postgres_url_sync` and `postgres_url_async` declared — same DB, different drivers. |
| Sync DB (consumers/detector/escalation) | `create_engine(settings.postgres_url_sync)` with `psycopg2-binary`. `sessionmaker` with context manager per write. No shared session across messages. |
| Async DB (API) | `create_async_engine(settings.postgres_url_async)` with `NullPool` in tests, `AsyncSession` via `get_db` dependency. |
| Boolean→float cast (SQL) | Use `correct::int::float` pattern in all raw SQL. Postgres cannot cast `boolean` directly to `double precision`. |
| Testing (Python) | Unit tests mock `confluent_kafka.Consumer`/`Producer` and `transformers.pipeline`. Integration tests use real Postgres on port 5434. `NullPool` on test engine. |
| Testing (frontend) | MSW for API mocking. No snapshot tests. Test loading, error, and data-populated states for each panel. |

---

## Implementation Notes for Implementer

**1. Do this first: case-queue source filter PR**
Add `source: str | None = None` to `list_cases()` in `projects/case-queue/api/app/routers/cases.py`. Add `if source is not None: filters.append(Case.source == source)` to `_build_filters`. Add one test. This unblocks the Human Review panel.

**2. Start from project 22**
Copy `projects/moderation-stream/` to `projects/moderation-dashboard/`. Rename package from `moderation_stream` to `moderation_dashboard` throughout. Then add: `group_id` param to `BaseConsumer.__init__`, `category` and `content` columns to the DB write and `ClassificationResult` type, `runner.py` CLI, anomaly detector, escalation service, dbt project, updated API routers, new React app.

**3. Kafka topic: 5 partitions**
In `docker-compose.yml` set `KAFKA_CREATE_TOPICS: "moderation-events:5:1"` (5 partitions, 1 replica). The existing project 22 topic had 1 partition — the new compose creates it fresh. Production consumers with 5 partitions and 3 processes receive partition assignments approximately 2+2+1; Phase 2 with 5 processes is exactly 1 per consumer.

**4. `content` in `classifications`**
Because the escalation service needs the event text to POST to case-queue, `content` must be stored in the `classifications` table alongside the classification result. Each consumer forwards `event.content` into the DB row. This is a small denormalisation but avoids requiring a raw events table.

**5. Sync vs async engine**
Consumers, anomaly detector, and escalation service are sync processes — they must use `create_engine(settings.postgres_url_sync)` with `psycopg2-binary`. Do not import or use `create_async_engine` or `asyncio` in these modules. The API exclusively uses `create_async_engine`. The ORM model classes (`Classification`, `AnomalyFlag`, `Escalation`) are shared but instantiated by whichever engine the process uses.

**6. Anomaly detector baseline**
Maintain `window_history: dict[str, list[float]]` — one entry per signal name. Skip Z-score check if `len(history[signal]) < settings.anomaly_min_history_windows` (default 10). Start accumulating on window 1; first check on window 11. This prevents false positives during warm-up.

**7. Escalation content lookup**
`_get_unevaluated_event_ids()` returns event_ids. To get `content` and `category` for the case-queue POST, query `classifications WHERE event_id = ? LIMIT 1` — `content` and `category` are the same across all classification rows for an event (forwarded from the original event message).

**8. Case-queue POST payload**
```python
{
    "content": event_content,
    "category": jigsaw_category_to_case_queue_category(category),  # map Jigsaw → CaseCategory enum
    "severity": infer_severity(confidence_max, reason),             # 'low' | 'medium' | 'high'
    "source": "moderation-dashboard",
    "meta": {
        "escalation_reason": reason,
        "confidence_max": confidence_max,
        "model_verdicts": {model_name: label for model_name, label in verdicts.items()},
    }
}
```
`category` mapping: Jigsaw labels → case-queue `CaseCategory` enum. They match exactly: `toxic`, `severe_toxic`, `obscene`, `threat`, `insult`, `identity_hate`. No mapping needed. `severity` heuristic: `high` if `severe_toxic` or `threat`; `medium` if `obscene` or `insult` or `identity_hate`; `low` otherwise.

**9. dbt `profiles.yml`**
Use `env_var()` calls — no hardcoded credentials. The dbt process reads from the same `.env` file as the rest of the project. `DBT_DB_*` env vars (host, port, user, password, dbname) are separate from the SQLAlchemy URLs to avoid parsing conflicts.

**10. API: `GET /metrics/production` and `/metrics/shadow`**
Always return all 5 MODEL_REGISTRY entries. For models with no rows in `classifications`, return the entry with `status=pending_weights` and all metric fields `null`. SQL: `GROUP BY model_name` then left-join with registry keys in Python.

**11. `GET /metrics/stream` event rate dedup**
Count unique `event_id` values (not total rows) in the last 60s to avoid triple-counting from shadow consumers: `SELECT COUNT(DISTINCT event_id) FROM classifications WHERE created_at >= NOW() - INTERVAL '60 seconds'`. Divide by 60 for per-second rate.

**12. Frontend dev port**
In `vite.config.ts`: `server: { port: 5174 }`. In `tsconfig.app.json`: remove `baseUrl` (TypeScript 6 breaks with `baseUrl` + `moduleResolution: bundler`). Use `paths: { "@/*": ["src/*"] }` only.

**13. Alembic**
Generate initial migration with `alembic revision --autogenerate -m "initial"` against live Postgres. All three tables (`classifications`, `anomaly_flags`, `escalations`) in one migration. Tests use `Base.metadata.create_all()` directly with a NullPool test engine — no Alembic in test setup.

---

## Handoff

**Next role:** design-brief (frontend has 5 panels — routing.md requires design-brief + frontend-architect before implementer for projects with a frontend)

**What design-brief does with this:**
- Locks in the visual layout of the 5-panel dashboard: tab navigation vs sidebar vs grid
- Specifies the primary interaction for each panel (read-only monitoring vs click-to-drill-down)
- Defines the key components needed (ModelCard, MetricChart, AnomalyBadge)
- Sets done criteria for the UI before frontend-architect specifies component hierarchy

**Flags for design-brief:**
- Model Performance and Model Comparison panels share the `ModelCard` component — design-brief should decide whether they are separate tabs or adjacent sections
- Human Review panel is read-only in the dashboard (links out to case-queue) — design-brief should confirm this interaction model
- Analytics panel has 3 charts — design-brief should confirm layout (stacked vs side-by-side)
- Stream Monitor is the "hero" panel — design-brief should decide if it is the default/landing view
