# Architect Output — moderation-stream

**Role:** architect
**Sequence:** `new-project-full` (step 3)
**Date:** 2026-06-02

---

## System Overview

Five independent Python processes consume a Kafka stream of Jigsaw toxic-comment events and write classification results to Postgres. A Kafka producer replays the Jigsaw CSV at configurable speed, publishing `ModerationEvent` JSON messages to the `moderation-events` topic. Three Phase 1 consumer processes (DistilBERT zero-shot, RoBERTa zero-shot, Detoxify) each run a blocking poll loop: receive message → run inference → write one `ClassificationResult` row to Postgres → commit offset. A FastAPI metrics service reads `classification_results` and computes per-model accuracy, latency percentiles, and throughput on demand. A new `/stream` React route added to the case-queue frontend polls the metrics API every 3 seconds and renders a five-card comparison panel. Phase 2 consumers (fine-tuned DistilBERT, fine-tuned RoBERTa) are present as processes but enter `pending_weights` mode when their checkpoint env vars are absent; the metrics API reflects this status from config, not from the database.

---

## Data Models

### Kafka Message — `ModerationEvent` (Pydantic, `moderation_stream.types`)

```python
class ModerationEvent(BaseModel):
    event_id: str                            # UUID v4, str representation
    text: str
    label: int | None = None                 # ground-truth label; None for live sources
    label_detail: dict[str, float] | None = None  # per-category scores; None for live sources
```

Serialised to JSON for Kafka. Producer calls `event.model_dump_json()`. Consumers call `ModerationEvent.model_validate_json(msg.value())`.

### Postgres ORM — `ClassificationResult` (`moderation_stream.api.models`)

```python
class ClassificationResult(Base):
    __tablename__ = "classification_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    predicted_label: Mapped[int] = mapped_column(nullable=False)
    latency_ms: Mapped[float] = mapped_column(nullable=False)
    correct: Mapped[bool | None] = mapped_column(nullable=True)  # None when label absent
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        Index("ix_cr_model_processed", "model_name", "processed_at"),
    )
```

Consumers write using sync SQLAlchemy (psycopg2 driver). FastAPI reads using async SQLAlchemy (asyncpg driver). The table is shared; the driver choice per-process is independent.

### Pydantic Response Schemas (`moderation_stream.api.schemas`)

```python
class ModelStatus(StrEnum):
    ACTIVE = "active"
    PENDING_WEIGHTS = "pending_weights"

class ModelMetrics(BaseModel):
    model_name: str
    status: ModelStatus
    total_processed: int
    correct: int | None        # None when no ground-truth labels present
    accuracy: float | None     # None when no ground-truth labels present
    p50_latency_ms: float      # 0.0 if no data
    p95_latency_ms: float      # 0.0 if no data
    throughput_cps: float      # classifications/sec over last 60s; 0.0 if no data

class MetricsResponse(BaseModel):
    models: list[ModelMetrics]
    generated_at: datetime
```

### TypeScript Types (`projects/case-queue/web/src/types/stream.ts`)

```typescript
export type ModelStatus = 'active' | 'pending_weights'

export type ModelMetrics = {
  model_name: string
  status: ModelStatus
  total_processed: number
  correct: number | null     // null when no ground-truth labels
  accuracy: number | null    // null when no ground-truth labels
  p50_latency_ms: number
  p95_latency_ms: number
  throughput_cps: number
}

export type MetricsResponse = {
  models: ModelMetrics[]
  generated_at: string   // ISO 8601
}
```

---

## Module Interfaces

### `moderation_stream.config`

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "moderation-events"

    # Sync URL (postgresql://...) — used by consumers and Alembic
    database_url: str

    # Async URL (postgresql+asyncpg://...) — used by FastAPI metrics API
    # If not set explicitly, derived from database_url by replacing scheme
    async_database_url: str | None = None

    jigsaw_csv_path: Path
    producer_rate_per_sec: int = 10  # messages/sec; CLI --limit overrides row count
    allowed_origin: str = "http://localhost:5173"

    # Phase 2 — unset → pending_weights mode
    distilbert_checkpoint_path: Path | None = None
    roberta_checkpoint_path: Path | None = None

    @property
    def effective_async_database_url(self) -> str:
        if self.async_database_url:
            return self.async_database_url
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    def phase2_status(self, checkpoint_path: Path | None) -> ModelStatus:
        return ModelStatus.ACTIVE if checkpoint_path else ModelStatus.PENDING_WEIGHTS
```

**Model registry** — static list consumed by the metrics router to build the full 5-model response regardless of which consumers are running:

```python
# In moderation_stream.config — not a Settings field; a module-level constant
MODEL_REGISTRY: list[dict[str, Any]] = [
    {"model_name": "distilbert-zero-shot",   "phase": 1},
    {"model_name": "roberta-zero-shot",      "phase": 1},
    {"model_name": "detoxify",               "phase": 1},
    {"model_name": "distilbert-finetuned",   "phase": 2, "checkpoint_field": "distilbert_checkpoint_path"},
    {"model_name": "roberta-finetuned",      "phase": 2, "checkpoint_field": "roberta_checkpoint_path"},
]
```

---

### `moderation_stream.producer`

```python
def create_producer(bootstrap_servers: str) -> Producer:
    """Return configured confluent-kafka Producer. Creates topic if absent."""

def load_jigsaw_csv(csv_path: Path, limit: int | None) -> Iterator[ModerationEvent]:
    """Yield ModerationEvent rows from Jigsaw CSV. Stops at limit if set."""

def publish_events(
    producer: Producer,
    events: Iterator[ModerationEvent],
    topic: str,
    rate_per_sec: int,
) -> int:
    """Publish events at rate_per_sec. Returns total published. Handles SIGINT."""

def main() -> None:
    """CLI entry point. Parses --limit. Prints stats on exit."""
```

Producer creates the `moderation-events` topic on first run using the admin client (`confluent_kafka.admin.AdminClient`). Key serialisation: `event_id` string. Value serialisation: `model_dump_json()`.

---

### `moderation_stream.consumers.base`

**Resolution of OQ1 and OQ3:** Consumers are fully synchronous. `BaseConsumer` owns the Kafka poll loop, latency measurement, and DB write. Subclasses implement only `_load_model()` and `_run_inference()`.

```python
class BaseConsumer(ABC):
    model_name: ClassVar[str]         # e.g. "distilbert-zero-shot"
    consumer_group_id: ClassVar[str]  # e.g. "consumer-distilbert"

    def __init__(self, settings: Settings) -> None:
        # Initialises sync SQLAlchemy engine + sessionmaker
        # Initialises confluent-kafka Consumer with auto.offset.reset=earliest
        # Calls self._load_model()

    @abstractmethod
    def _load_model(self) -> None:
        """Load model weights into memory. Called once during __init__."""

    @abstractmethod
    def _run_inference(self, text: str) -> int:
        """Run inference. Return predicted_label (0 or 1)."""

    def classify(self, text: str) -> tuple[int, float]:
        """Wraps _run_inference with perf_counter latency measurement."""
        start = time.perf_counter()
        label = self._run_inference(text)
        latency_ms = (time.perf_counter() - start) * 1000.0
        return label, latency_ms

    def _write_result(self, result: ClassificationResult) -> None:
        """Sync session write + commit."""

    def run(self) -> None:
        """Blocking poll loop. Subscribes to topic. Handles SIGINT gracefully."""
        # poll(timeout=1.0) → skip if None
        # deserialise → classify → write → commit offset (synchronous=False)
        # correct = (predicted_label == event.label) if event.label is not None else None
```

`SIGINT` handler sets a `_running = False` flag; the poll loop exits after the current message completes. The consumer calls `self._consumer.close()` before exit.

Offset commit strategy: commit after each message (`synchronous=False` for throughput; synchronous commit on shutdown). At the target rate (10 msg/sec), per-message commits are fine.

---

### `moderation_stream.consumers.distilbert`

```python
class DistilBertZeroShotConsumer(BaseConsumer):
    model_name = "distilbert-zero-shot"
    consumer_group_id = "consumer-distilbert"
    # Model: pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli", device=-1)
    # candidate_labels = ["toxic content", "safe content"]
    # predicted_label = 1 if labels[0] == "toxic content" and scores[0] > 0.5 else 0

    def _load_model(self) -> None: ...
    def _run_inference(self, text: str) -> int: ...

def main() -> None: ...
```

---

### `moderation_stream.consumers.roberta`

```python
class RobertaZeroShotConsumer(BaseConsumer):
    model_name = "roberta-zero-shot"
    consumer_group_id = "consumer-roberta"
    # Model: pipeline("zero-shot-classification", model="roberta-large-mnli", device=-1)
    # Same candidate_labels + threshold as DistilBERT consumer

    def _load_model(self) -> None: ...
    def _run_inference(self, text: str) -> int: ...

def main() -> None: ...
```

---

### `moderation_stream.consumers.detoxify_consumer`

```python
class DetoxifyConsumer(BaseConsumer):
    model_name = "detoxify"
    consumer_group_id = "consumer-detoxify"
    # Model: Detoxify("original", device="cpu")
    # predicted_label = 1 if result["toxicity"] >= 0.5 else 0
    # Note: Detoxify returns a dict of scores; use "toxicity" key only for binary label

    def _load_model(self) -> None: ...
    def _run_inference(self, text: str) -> int: ...

def main() -> None: ...
```

---

### `moderation_stream.consumers.finetuned`

```python
class FinetunedConsumer(BaseConsumer):
    # Shared base for both Phase 2 consumers.
    # model_name and consumer_group_id set by subclass.
    # checkpoint_path: Path | None — if None, run() logs warning and returns immediately without polling.
    # Model: pipeline("text-classification", model=str(checkpoint_path), device=-1)
    # Output label mapping: model returns "LABEL_1"/"LABEL_0" or "toxic"/"not toxic" depending on
    # how project 8 exports — implementer must confirm label mapping at integration time.

    def __init__(self, settings: Settings, checkpoint_path: Path | None) -> None: ...
    def _load_model(self) -> None: ...
    def _run_inference(self, text: str) -> int: ...
    def run(self) -> None:  # overrides base: exits immediately if no checkpoint

class FinetunedDistilBertConsumer(FinetunedConsumer):
    model_name = "distilbert-finetuned"
    consumer_group_id = "consumer-distilbert-ft"

class FinetunedRobertaConsumer(FinetunedConsumer):
    model_name = "roberta-finetuned"
    consumer_group_id = "consumer-roberta-ft"

def main_distilbert() -> None: ...
def main_roberta() -> None: ...
```

---

### `moderation_stream.api.database`

```python
def create_async_engine_from_settings(settings: Settings) -> AsyncEngine: ...

def get_async_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]: ...

async def init_db(engine: AsyncEngine) -> None:
    """Create tables if they do not exist (for dev). Production uses Alembic."""

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency. Yields a session per request."""
```

---

### `moderation_stream.api.routers.metrics`

**Resolution of OQ2:** Single SQL query using `GROUP BY model_name` with Postgres aggregate functions. Index `ix_cr_model_processed` on `(model_name, processed_at)` covers the throughput window filter. Percentile calculation scans all rows per model — acceptable at Phase 1 scale (≤1 000 events per model). At full dataset scale (~160K rows per model), add a materialized view refreshed every 30 seconds (defer to Phase 2).

```python
# Core metrics SQL — executed once per GET /metrics request
METRICS_SQL = text("""
    SELECT
        model_name,
        COUNT(*)                                                            AS total_processed,
        SUM(correct::int)                                                   AS correct,   -- NULL when no labelled rows
        AVG(correct::float)                                                 AS accuracy,  -- NULL when no labelled rows
        COALESCE(percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms), 0) AS p50_latency_ms,
        COALESCE(percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms), 0) AS p95_latency_ms,
        COALESCE(
            COUNT(*) FILTER (WHERE processed_at >= NOW() - INTERVAL '60 seconds') / 60.0,
            0
        )                                                                   AS throughput_cps
    FROM classification_results
    GROUP BY model_name
""")

async def get_metrics(db: AsyncSession, settings: Settings) -> MetricsResponse:
    """
    Query DB for all active models, merge with MODEL_REGISTRY for Phase 2 status.
    Returns all 5 model entries; pending Phase 2 models get zeroed metrics.
    """
```

Router:
```python
router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("", response_model=MetricsResponse)
async def read_metrics(db: AsyncSession = Depends(get_db)) -> MetricsResponse: ...

@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

---

### `moderation_stream.api.main`

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db(engine)
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.allowed_origin], ...)
app.include_router(metrics_router)
```

---

### React: `src/api/stream.ts`

```typescript
const STREAM_API_BASE = import.meta.env.VITE_STREAM_API_URL  // e.g. http://localhost:8001

async function fetchMetrics(): Promise<MetricsResponse> {
  // Plain fetch — no X-Actor headers needed (read-only monitoring)
  const res = await fetch(`${STREAM_API_BASE}/metrics`)
  if (!res.ok) throw new Error(`Metrics API error: ${res.status}`)
  return res.json() as Promise<MetricsResponse>
}

export function useStreamMetrics(): UseQueryResult<MetricsResponse, Error> {
  return useQuery({
    queryKey: ['stream-metrics'],
    queryFn: fetchMetrics,
    refetchInterval: 3000,
    retry: 2,
  })
}
```

---

### React: `src/components/ModelMetricsCard.tsx`

```typescript
type ModelMetricsCardProps = {
  metrics: ModelMetrics
}

// Renders a shadcn/ui Card:
// Header: model_name + status Badge ("Active" green / "Pending Weights" grey)
// Body (pending): single line "Awaiting fine-tuned weights from project 8"
// Body (active): accuracy %, p50 ms, p95 ms, throughput cps, total processed
```

---

### React: `src/pages/StreamDashboard.tsx`

```typescript
// Route: /stream
// - Calls useStreamMetrics()
// - Loading: spinner or skeleton on first load (isLoading && !data)
// - Error: <ErrorMessage> when error is set and no data
// - Success: <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
//     {data.models.map(m => <ModelMetricsCard key={m.model_name} metrics={m} />)}
//   </div>
// - Last updated timestamp from data.generated_at
```

---

## Dependencies

```
Producer
  → confluent-kafka (write to moderation-events topic)
  → ModerationEvent (moderation_stream.types)

BaseConsumer / Subclasses
  → confluent-kafka (read from moderation-events topic)
  → ModerationEvent (moderation_stream.types)
  → ClassificationResult ORM (moderation_stream.api.models — shared model, sync session)
  → Settings (moderation_stream.config)

Metrics API
  → ClassificationResult ORM (moderation_stream.api.models — async session)
  → Settings + MODEL_REGISTRY (moderation_stream.config)
  → ModelMetrics, MetricsResponse schemas (moderation_stream.api.schemas)

React StreamDashboard
  → useStreamMetrics (src/api/stream.ts)
  → MetricsResponse, ModelMetrics (src/types/stream.ts)
  → ModelMetricsCard (src/components/ModelMetricsCard.tsx)
  → ErrorMessage (existing src/components/ErrorMessage.tsx)
```

**Potential coupling issue:** Consumers import `ClassificationResult` from `moderation_stream.api.models` to use the ORM model. This couples the consumer package to the API package. Acceptable here — both live in the same project. If they were separate services, the ORM model would move to `moderation_stream.models`.

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Error handling (Python) | Specific exceptions with `from exc` chaining. Consumers catch `KafkaError` and log; do not crash the loop on a single message failure. Fatal errors (DB connection lost) propagate to top-level and kill the process — let the Makefile restart it. |
| Configuration | `pydantic-settings` loaded once at module level in each process. `Settings()` is passed to constructors — no global state access inside functions. |
| Logging | Python `logging` stdlib. `basicConfig(level=INFO)`. Each consumer logs model_name, event_id, latency on every 100th message (not every message — avoid log flood at 10 msg/sec). |
| Dual ORM | Consumers: `create_engine(settings.database_url)` + `sessionmaker` (psycopg2). API: `create_async_engine(settings.effective_async_database_url)` + `async_sessionmaker` (asyncpg). Never mix drivers. Alembic uses the sync URL. |
| Alembic | Async migration runner pattern from case-queue (`asyncio.run(run_migrations_online())` with `async_engine_from_config`). `env.py` imports `Base.metadata` from `moderation_stream.api.models`. |
| Testing (Python) | Unit tests mock Kafka Producer/Consumer at the confluent-kafka boundary using `unittest.mock`. API tests use `httpx.AsyncClient` against a test DB (`moderation_stream_test`). Consumer tests inject a pre-built sync session. |
| Testing (React) | `msw` mocks `GET /metrics`. Tests verify card renders for both `active` and `pending_weights` status. Tests verify error state renders when fetch fails. |

---

## Implementation Notes for Implementer

1. **`librdkafka` prerequisite.** Document in README: `brew install librdkafka` (macOS) or `apt install librdkafka-dev` (Linux) before `uv sync`. Without this, `uv add confluent-kafka` succeeds but import fails.

2. **Model loading latency.** Each HuggingFace transformer downloads weights on first `_load_model()` call (~250–700 MB per model). Subsequent runs use the HuggingFace cache (`~/.cache/huggingface/`). Add a log line "Loading model…" and "Model ready" so the operator sees startup progress. For tests, use a tiny local mock model or monkeypatch `_run_inference`.

3. **Detoxify returns a dict.** `Detoxify("original").predict(text)` returns `{"toxicity": float, "severe_toxicity": float, ...}`. Use only `result["toxicity"]` for `predicted_label`. Threshold 0.5.

4. **Zero-shot label order is not guaranteed.** When using `pipeline("zero-shot-classification")`, the returned `labels` list is sorted by score descending, not by the order you passed `candidate_labels`. Always find the score for `"toxic content"` by matching the label string, not by index.

5. **`VITE_STREAM_API_URL` env var.** Add to `projects/case-queue/web/.env.example`. The frontend `.env` already has `VITE_API_URL` for the case-queue API; the stream metrics API runs on a different port (8001 default).

6. **Postgres schema for `moderation_stream_db`.** Docker Compose Postgres `POSTGRES_DB` creates one database. The consumer and API both need `moderation_stream_db`. Either set `POSTGRES_DB=moderation_stream_db` in docker-compose, or run `CREATE DATABASE moderation_stream_db` in an init script. Use an `init.sql` file mounted into the Postgres container.

7. **`percentile_cont` requires at least one row.** Wrap all aggregate columns with `COALESCE(..., 0)` (already shown in the SQL above) to handle the case where a consumer has not processed any events yet.

8. **Alembic migration.** `alembic revision --autogenerate -m "initial"` requires a live Postgres connection to `moderation_stream_db`. Run it once after `docker compose up`. Commit the generated migration file.

9. **Makefile `make consumers` target.** Start all three Phase 1 consumers in background (`&`) with output redirected to per-model log files. Add a `make stop` target that kills all background jobs by process group.

10. **Nav link placement.** The `/stream` nav link in case-queue goes alongside the existing links. Use the existing nav component pattern — do not add a new nav component.

---

## Handoff

**Next role:** implementer
**What the implementer does with this output:**
- Scaffold the `projects/moderation-stream/` uv project using `skills/setup-uv-project.md`.
- Implement all modules in the order: `config.py` → `types.py` → `api/models.py` → `producer.py` → `consumers/base.py` → consumers (distilbert, roberta, detoxify) → `api/` (database, schemas, router, main) → Makefile/docker-compose → tests.
- Add the frontend additions to `projects/case-queue/web/src/` (types, hook, card, dashboard, App.tsx modification).
- Run `uv run pytest` and `pnpm test` before marking implementation complete.

**Flags for implementer:**
- Implementation note 4 (zero-shot label order) will cause a silent accuracy bug if missed — read it.
- Implementation note 2 (model download) means the first `make consumers` run takes several minutes — this is expected.
- The finetuned consumer's label mapping (note: "LABEL_1"/"LABEL_0" vs "toxic"/"not toxic") cannot be confirmed until project 8 completes; leave a `# TODO: confirm label mapping with project 8 output` comment in `finetuned.py`.
- Dual ORM pattern (sync consumers, async API) is not a mistake — do not "fix" it.
