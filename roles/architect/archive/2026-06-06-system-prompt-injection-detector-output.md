# Architect Output — system-prompt-injection-detector

**Role:** architect
**Sequence:** `new-project-full` (step 3)
**Date:** 2026-06-06

---

## System Overview

The system-prompt-injection-detector consists of two Python projects and one React SPA. The training project (`injection-detector-training/`) is a standalone uv project that: (1) generates synthetic benign examples via Ollama, (2) downloads and merges the SPML injection benchmark with those negatives, (3) fine-tunes `distilbert-base-uncased` via HuggingFace `Trainer` on MPS, and (4) evaluates the checkpoint and writes an eval JSON to the shared `resources/evals/` directory. The detection service (`injection-detector/`) is a FastAPI application that loads the trained checkpoint once at startup, exposes a `/detect` endpoint that scores each field of an incoming agent request independently, a `/proxy` endpoint that either blocks or forwards requests to a downstream LLM based on detection results, and a set of read endpoints for the React dashboard. Every detection attempt is written synchronously to a `detection_log` Postgres table (port 5438). The dashboard (`injection-detector-dashboard/`) is a separate Vite/React SPA that displays detection history, per-field flag rates, injection probability distributions, and the model card with calibration data via TanStack Query hooks against the service API.

---

## Open Questions Resolved

**OQ1 — SPML dataset field names:**
The `reshabhs/SPML_Chatbot_Prompt_Injection` dataset uses two columns: `prompt` (the text) and `label` (0=benign, 1=injection). This matches the dataset card description. Implementer must verify by running:
```python
from datasets import load_dataset
ds = load_dataset("reshabhs/SPML_Chatbot_Prompt_Injection")
print(ds["train"].features)
print(ds["train"][0])
```
If the column names differ, update `load_spml()` before proceeding. The architect specifies `prompt` and `label` as the expected names; this is the single field name assumption the implementer must confirm.

**OQ2 — Confidence distribution data source:**
Add a dedicated `GET /logs/probabilities` endpoint that returns `list[ProbabilityPoint]` where each point is `{probability: float, flagged: bool}`. This is cleaner than embedding bin computation in `/logs/stats`. The React component bins the data client-side into 10 equal-width buckets. This keeps the server stateless for this query and avoids a second data shape in the stats endpoint.

**OQ3 — Classifier startup failure mode:**
Fail-fast on startup. The lifespan raises `RuntimeError` if `MODEL_CHECKPOINT_DIR` is not set or the directory does not contain `config.json`. The app does not start. This matches workspace convention: raise on uninitialised state, never return a silent default.

**OQ4 — Proxy body passthrough:**
The proxy forwards raw request bytes. `POST /proxy` reads the raw request body bytes (not the parsed `DetectionRequest`), calls `run_detection()` with the parsed `DetectionRequest`, and if not flagged, issues `httpx.AsyncClient.post(DOWNSTREAM_LLM_URL, content=raw_body, headers={"Content-Type": "application/json"})`. The response status code and body are returned unchanged. The caller is responsible for sending a body the downstream LLM understands. This keeps the proxy format-agnostic.

**OQ5 — async vs sync SQLAlchemy:**
Async throughout. `AsyncSession` with `async_sessionmaker`, injected via FastAPI `Depends`. All DB calls use `await session.execute(...)`. Consistent with FastAPI async handlers and asyncpg.

---

## Data Models

### Training Project

#### `EvalResult` (dataclass — `metrics.py`)

```python
@dataclass
class EvalResult:
    model_key: str              # e.g. "distilbert-base-uncased"
    checkpoint_dir: str         # absolute path
    f1: float
    precision: float
    recall: float
    auc_roc: float
    calibration_bins: list[CalibrationBin]  # 10 bins
    evaluated_at: str           # ISO 8601 UTC timestamp
```

#### `CalibrationBin` (dataclass — `metrics.py`)

```python
@dataclass
class CalibrationBin:
    bin_lower: float            # e.g. 0.0
    bin_upper: float            # e.g. 0.1
    count: int                  # total samples in this bin
    mean_predicted_probability: float
    fraction_of_positives: float
```

#### Eval JSON schema (written to `resources/evals/injection-detector-training/`)

The `EvalResult` dataclass is serialised to JSON via `dataclasses.asdict()`. Filename: `distilbert-base-uncased-<YYYYMMDD-HHMMSS>.json`.

### Detection Service

#### `DetectionRequest` (Pydantic — `models.py`)

```python
class DetectionRequest(BaseModel):
    system_prompt: str
    user_message: str
    tool_outputs: list[str] = []
```

#### `FieldResult` (Pydantic — `models.py`)

```python
class FieldResult(BaseModel):
    field_name: str             # "system_prompt" | "user_message" | "tool_output_0" | ...
    injection_probability: float
    flagged: bool               # injection_probability >= INJECTION_THRESHOLD
```

#### `DetectionResponse` (Pydantic — `models.py`)

```python
class DetectionResponse(BaseModel):
    fields: list[FieldResult]
    overall_flagged: bool       # True if any field is flagged
    max_probability: float      # max(f.injection_probability for f in fields)
```

#### `ProbabilityPoint` (Pydantic — `models.py`)

```python
class ProbabilityPoint(BaseModel):
    probability: float
    flagged: bool
```

#### `DetectionLog` (SQLAlchemy ORM — `db/orm.py`)

```python
class DetectionLog(Base):
    __tablename__ = "detection_log"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    request_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # Full DetectionRequest as JSONB. Stores system_prompt, user_message, tool_outputs.
    overall_flagged: Mapped[bool] = mapped_column(Boolean, nullable=False)
    max_probability: Mapped[float] = mapped_column(Float, nullable=False)
    field_results: Mapped[list] = mapped_column(JSONB, nullable=False)
    # List of FieldResult dicts. Variable length — tool_outputs[i] appear as tool_output_i.
    detected_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, nullable=False, default=lambda: datetime.now(UTC)
    )
```

#### `Settings` (pydantic-settings — `config.py`, both projects)

Training:
```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"
    spml_dataset_name: str = "reshabhs/SPML_Chatbot_Prompt_Injection"
    negatives_path: Path = Path("data/negatives.jsonl")
    checkpoint_output_dir: Path = Path("../../resources/models/injection-detector-training")
    evals_output_dir: Path = Path("../../resources/evals/injection-detector-training")
    training_seed: int = 42
    num_train_epochs: int = 4
    per_device_train_batch_size: int = 64
    warmup_steps: int = 100
```

Service:
```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str                       # asyncpg DSN, port 5438
    model_checkpoint_dir: Path
    injection_threshold: float = 0.7
    downstream_llm_url: str | None = None   # required for /proxy to function
    evals_dir: Path = Path("../../resources/evals/injection-detector-training")
```

---

## DB Schema

```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE detection_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_json    JSONB NOT NULL,
    overall_flagged BOOLEAN NOT NULL,
    max_probability FLOAT NOT NULL,
    field_results   JSONB NOT NULL,
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Fast time-range queries (dashboard default view, daily stats)
CREATE INDEX idx_detection_log_detected_at ON detection_log (detected_at DESC);

-- Filter by flagged status (Detection Log tab's flagged_only toggle)
CREATE INDEX idx_detection_log_overall_flagged ON detection_log (overall_flagged);

-- JSON path query for field-level analysis (field_results[*].field_name, flagged)
CREATE INDEX idx_detection_log_field_results ON detection_log USING GIN (field_results);
```

Alembic manages migrations. Initial migration creates the table and indexes.

---

## Module Interfaces

### `injection-detector-training/`

#### `dataset.py`

```python
def load_spml(dataset_name: str) -> datasets.Dataset:
    """
    Load the SPML dataset from HuggingFace and return a Dataset with
    columns renamed to {"text": ..., "label": ...}.
    Source columns: "prompt" (str) and "label" (int, 0=benign 1=injection).
    Implementer must confirm column names before writing this function.
    """
    ...

def load_negatives(path: Path) -> datasets.Dataset:
    """
    Load the synthetic negatives JSONL file.
    Each line: {"text": str, "label": 0}.
    Returns a Dataset with columns {"text": str, "label": int}.
    Raises FileNotFoundError if path does not exist (not a silent default).
    """
    ...

def build_dataset(
    spml: datasets.Dataset,
    negatives: datasets.Dataset,
    seed: int = 42,
) -> datasets.DatasetDict:
    """
    Concatenate spml and negatives, shuffle with seed, split 80/10/10.
    Returns DatasetDict with keys: "train", "validation", "test".
    """
    ...

def tokenize_dataset(
    dataset_dict: datasets.DatasetDict,
    tokenizer: PreTrainedTokenizer,
    max_length: int = 512,
) -> datasets.DatasetDict:
    """
    Apply tokenizer to "text" column. Returns dataset with input_ids,
    attention_mask, label columns. Removes "text" column.
    """
    ...
```

#### `generate_negatives.py`

```python
def generate_negative(client: httpx.Client, model: str, ollama_base_url: str) -> str:
    """
    Call Ollama generate endpoint once with the benign prompt template.
    Returns the generated text string.
    Raises httpx.HTTPError on failure.
    Prompt template:
      "Generate a normal user message to an AI assistant. The message should be
       a genuine request, not containing any instructions to override system prompts.
       Length: 1-3 sentences. Output only the message text, no quotes or labels."
    """
    ...

def generate_negatives_batch(
    count: int,
    ollama_base_url: str,
    model: str,
    output_path: Path,
) -> None:
    """
    Call generate_negative() count times. Write results to output_path as JSONL.
    Each line: {"text": "...", "label": 0}.
    Logs progress every 100 samples.
    Raises RuntimeError if Ollama is not reachable (connection refused).
    """
    ...

# CLI entry point registered in pyproject.toml:
# [project.scripts]
# generate-negatives = "injection_detector_training.generate_negatives:cli"
def cli() -> None:
    """
    Typer CLI. --count (int, default 5000), --output (Path, default data/negatives.jsonl).
    Calls generate_negatives_batch().
    """
    ...
```

#### `metrics.py`

```python
def compute_metrics(eval_pred: EvalPrediction) -> dict[str, float]:
    """
    HuggingFace Trainer compute_metrics callback.
    Returns {"f1": float, "precision": float, "recall": float}.
    Uses sklearn.metrics with average="binary".
    """
    ...

def compute_calibration_bins(
    probabilities: list[float],
    labels: list[int],
    n_bins: int = 10,
) -> list[CalibrationBin]:
    """
    Compute calibration bins with n_bins equal-width buckets from 0.0 to 1.0.
    For each bin: count, mean predicted probability, fraction of positives.
    Empty bins have mean_predicted_probability=0.0 and fraction_of_positives=0.0.
    """
    ...

def compute_auc_roc(probabilities: list[float], labels: list[int]) -> float:
    """
    Compute AUC-ROC using sklearn.metrics.roc_auc_score.
    """
    ...
```

#### `train.py`

```python
# CLI entry point: uv run train
def cli() -> None:
    """
    Typer CLI. No required flags — all config from Settings (reads .env).
    Process:
      1. Load settings
      2. Load SPML dataset and negatives
      3. Build combined dataset
      4. Load tokenizer (distilbert-base-uncased)
      5. Tokenize dataset
      6. Load AutoModelForSequenceClassification (num_labels=2)
      7. Configure TrainingArguments:
           output_dir=<checkpoint_dir>,
           num_train_epochs=settings.num_train_epochs,
           per_device_train_batch_size=settings.per_device_train_batch_size,
           eval_strategy="epoch", save_strategy="epoch",
           load_best_model_at_end=True, metric_for_best_model="eval_f1",
           warmup_steps=settings.warmup_steps,
           seed=settings.training_seed
         (No no_cuda, no bf16, no pin_memory)
      8. Create Trainer, call trainer.train()
      9. Save best model via model.save_pretrained() + tokenizer.save_pretrained()
         to checkpoint_dir = settings.checkpoint_output_dir / f"distilbert-base-uncased-{date}"
    """
    ...
```

#### `evaluate.py`

```python
# CLI entry point: uv run evaluate
def cli() -> None:
    """
    Typer CLI. --checkpoint-dir (Path, required).
    Process:
      1. Load model and tokenizer from checkpoint_dir
      2. Load test split (rebuild dataset to get the same seed split)
      3. Run inference on all test examples, collect logits
      4. Softmax logits to get injection_probability (index 1)
      5. Compute metrics: F1, precision, recall, AUC-ROC via metrics.py
      6. Compute calibration bins via compute_calibration_bins()
      7. Build EvalResult dataclass
      8. Write to evals_output_dir / f"distilbert-base-uncased-{timestamp}.json"
      9. Print summary table to stdout
    """
    ...
```

### `injection-detector/`

#### `classifier.py`

```python
class Classifier:
    """
    Wraps the loaded DistilBERT checkpoint. Loaded once at startup.
    Not a singleton — owned by the lifespan context and injected via app.state.
    """

    def __init__(self, checkpoint_dir: Path) -> None:
        """
        Load tokenizer and model from checkpoint_dir.
        Raises RuntimeError if config.json is not found in checkpoint_dir.
        """
        ...

    def predict_field(self, text: str) -> float:
        """
        Tokenize text, run inference, return injection_probability (float 0.0–1.0).
        Softmax over logits; returns logits[1] after softmax.
        Thread-safe: no mutable state modified during inference.
        """
        ...

    def predict_all(
        self,
        request: DetectionRequest,
        threshold: float,
    ) -> DetectionResponse:
        """
        Score system_prompt, user_message, and each element of tool_outputs.
        Field names: "system_prompt", "user_message", "tool_output_0", "tool_output_1", ...
        Build list[FieldResult]. Compute overall_flagged, max_probability.
        Return DetectionResponse.
        """
        ...
```

#### `detection.py`

```python
async def run_detection(
    request: DetectionRequest,
    classifier: Classifier,
    session: AsyncSession,
    threshold: float,
) -> DetectionResponse:
    """
    1. Call classifier.predict_all(request, threshold)
    2. Persist to detection_log:
         DetectionLog(
             request_json=request.model_dump(),
             overall_flagged=response.overall_flagged,
             max_probability=response.max_probability,
             field_results=[f.model_dump() for f in response.fields],
         )
    3. Return response.
    Pure business logic — no HTTP concerns. Used by both /detect and /proxy.
    """
    ...
```

#### `routers/detect.py`

```python
@router.post("/detect", response_model=DetectionResponse)
async def detect(
    request: DetectionRequest,
    classifier: Annotated[Classifier, Depends(get_classifier)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DetectionResponse:
    """Scores all fields of the request. Logs to DB. Returns DetectionResponse."""
    ...

@router.post("/proxy")
async def proxy(
    raw_request: Request,
    classifier: Annotated[Classifier, Depends(get_classifier)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Response:
    """
    1. Parse raw body as DetectionRequest (raise HTTP 422 if invalid JSON).
    2. Call run_detection() with the parsed request.
    3. If response.overall_flagged: raise HTTPException(status_code=400, detail=response.model_dump())
    4. If not flagged: POST raw_body bytes to settings.downstream_llm_url via httpx.
       Return upstream response as FastAPI Response (preserve status_code and body).
    5. If settings.downstream_llm_url is None: raise HTTPException(503, "DOWNSTREAM_LLM_URL not configured")
    """
    ...
```

#### `routers/logs.py`

```python
@router.get("/logs", response_model=LogsResponse)
async def get_logs(
    page: int = 1,
    page_size: int = 50,
    flagged_only: bool = False,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LogsResponse:
    """
    Paginated DetectionLog records, ordered by detected_at DESC.
    flagged_only: if True, filter WHERE overall_flagged = true.
    LogsResponse = {"items": list[DetectionLogSchema], "total": int, "page": int, "page_size": int}
    """
    ...

@router.get("/logs/stats", response_model=LogsStats)
async def get_logs_stats(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LogsStats:
    """
    Returns:
    - total_detections: int
    - total_flagged: int
    - flag_rate: float (total_flagged / total_detections or 0.0)
    - field_flag_rates: dict[str, float]  # field_name -> flag rate
      Computed by unnesting field_results JSONB array and grouping by field_name.
      SQL: SELECT elem->>'field_name', AVG((elem->>'flagged')::boolean::int)
           FROM detection_log, jsonb_array_elements(field_results) AS elem
           GROUP BY 1
    - daily_counts: list[DailyCount]  # last 30 days, [{date: str, total: int, flagged: int}]
    """
    ...

@router.get("/logs/probabilities", response_model=list[ProbabilityPoint])
async def get_probabilities(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ProbabilityPoint]:
    """
    Returns all {max_probability, overall_flagged} pairs from detection_log.
    Used by ConfidenceHistogram to bin client-side.
    No pagination — intended for chart use. Cap at 10,000 most recent records.
    """
    ...

@router.get("/eval", response_model=EvalResultSchema)
async def get_eval(
    settings: Annotated[Settings, Depends(get_settings)],
) -> EvalResultSchema:
    """
    Read latest eval JSON from settings.evals_dir (sorted by filename timestamp, descending).
    Returns parsed EvalResult as JSON.
    Raises HTTP 404 if no eval files exist.
    """
    ...
```

#### Supporting types in `routers/logs.py`

```python
class DetectionLogSchema(BaseModel):
    id: UUID
    overall_flagged: bool
    max_probability: float
    field_results: list[FieldResult]
    detected_at: datetime

class LogsResponse(BaseModel):
    items: list[DetectionLogSchema]
    total: int
    page: int
    page_size: int

class DailyCount(BaseModel):
    date: str   # YYYY-MM-DD
    total: int
    flagged: int

class LogsStats(BaseModel):
    total_detections: int
    total_flagged: int
    flag_rate: float
    field_flag_rates: dict[str, float]
    daily_counts: list[DailyCount]

class EvalResultSchema(BaseModel):
    model_key: str
    checkpoint_dir: str
    f1: float
    precision: float
    recall: float
    auc_roc: float
    calibration_bins: list[CalibrationBinSchema]
    evaluated_at: str

class CalibrationBinSchema(BaseModel):
    bin_lower: float
    bin_upper: float
    count: int
    mean_predicted_probability: float
    fraction_of_positives: float
```

#### `main.py`

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    On startup:
      1. Validate MODEL_CHECKPOINT_DIR is set and config.json exists. Raise RuntimeError if not.
      2. Load Classifier — stores in app.state.classifier
      3. Create DB tables (Alembic in production; create_all for dev)
    On shutdown: close DB engine.
    """
    ...

app = FastAPI(title="Injection Detector", lifespan=lifespan)
app.include_router(detect_router)
app.include_router(logs_router)
```

### `injection-detector-dashboard/`

#### `types/api.ts`

```typescript
export type FieldResult = {
  field_name: string
  injection_probability: number
  flagged: boolean
}

export type DetectionLogItem = {
  id: string
  overall_flagged: boolean
  max_probability: number
  field_results: FieldResult[]
  detected_at: string   // ISO 8601
}

export type LogsResponse = {
  items: DetectionLogItem[]
  total: number
  page: number
  page_size: number
}

export type DailyCount = {
  date: string
  total: number
  flagged: number
}

export type LogsStats = {
  total_detections: number
  total_flagged: number
  flag_rate: number
  field_flag_rates: Record<string, number>
  daily_counts: DailyCount[]
}

export type ProbabilityPoint = {
  probability: number
  flagged: boolean
}

export type CalibrationBin = {
  bin_lower: number
  bin_upper: number
  count: number
  mean_predicted_probability: number
  fraction_of_positives: number
}

export type EvalResult = {
  model_key: string
  checkpoint_dir: string
  f1: number
  precision: number
  recall: number
  auc_roc: number
  calibration_bins: CalibrationBin[]
  evaluated_at: string
}
```

#### Hooks (`hooks/`)

```typescript
// useLogs.ts
export function useLogs(params: {
  page: number
  page_size?: number
  flagged_only?: boolean
}): UseQueryResult<LogsResponse>
// GET /logs?page=N&page_size=50&flagged_only=false

// useLogStats.ts
export function useLogStats(): UseQueryResult<LogsStats>
// GET /logs/stats

// useProbabilities.ts
export function useProbabilities(): UseQueryResult<ProbabilityPoint[]>
// GET /logs/probabilities

// useEval.ts
export function useEval(): UseQueryResult<EvalResult>
// GET /eval
```

#### Components

**`DetectionLogTable.tsx`**
Props: `{ page: number; onPageChange: (p: number) => void; flaggedOnly: boolean; onFlaggedOnlyChange: (v: boolean) => void }`
- Renders a `<table>` with columns: Timestamp, Flagged (badge), Max Probability, Fields (expand toggle).
- Expanded row: list of `FieldResult` entries with field_name and probability bar.
- flaggedOnly filter: dropdown (`<select>`) with values "All" / "Flagged Only" (queryable set — not text input).
- Uses `useLogs()` hook. Shows loading skeleton and error state.

**`FieldAnalysisChart.tsx`**
Props: none (fetches internally via `useLogStats()`)
- recharts `BarChart` (horizontal or vertical, vertical preferred for field names as labels).
- Data: `LogsStats.field_flag_rates` mapped to `[{field: string, flag_rate: number}]`.
- X-axis: field names. Y-axis: flag rate (0–100%).
- Single `<Bar dataKey="flag_rate" fill="#ef4444" />` (red for injection flags).

**`ConfidenceHistogram.tsx`**
Props: none (fetches internally via `useProbabilities()`)
- Client-side bins the `ProbabilityPoint[]` into 10 equal-width buckets [0.0–0.1, …, 0.9–1.0].
- Binning logic:
  ```typescript
  const bins = Array.from({ length: 10 }, (_, i) => ({
    range: `${(i * 0.1).toFixed(1)}–${((i + 1) * 0.1).toFixed(1)}`,
    flagged: 0,
    benign: 0,
  }))
  for (const p of data) {
    const idx = Math.min(Math.floor(p.probability * 10), 9)
    if (p.flagged) bins[idx].flagged++ else bins[idx].benign++
  }
  ```
- recharts `BarChart` with two `<Bar>` series: `flagged` (red `#ef4444`) and `benign` (green `#22c55e`).
- X-axis: bin range label. Y-axis: count.
- `<Legend />` showing Flagged / Benign.

**`ModelCard.tsx`**
Props: none (fetches internally via `useEval()`)
- Displays F1, precision, recall, AUC-ROC as a 4-column metric grid.
- Calibration chart: recharts `BarChart`. X-axis: bin range. Two lines overlaid:
  - `<Bar dataKey="mean_predicted_probability" fill="#6366f1" name="Mean Predicted" />`
  - `<Bar dataKey="fraction_of_positives" fill="#f59e0b" name="Fraction Positive" />`
  - A perfect-calibration diagonal would show both bars equal height.
- Shows `evaluated_at` timestamp below the metrics.

---

## Dependencies (Import Graph)

```
injection-detector-training/
  generate_negatives.py → config.py
  dataset.py            → [no internal deps; uses datasets, pathlib]
  metrics.py            → [no internal deps; uses sklearn]
  train.py              → config.py, dataset.py, metrics.py
  evaluate.py           → config.py, dataset.py, metrics.py
  tests/*               → dataset.py, generate_negatives.py, metrics.py, evaluate.py

injection-detector/
  db/engine.py          → config.py
  db/orm.py             → db/engine.py
  classifier.py         → models.py (DetectionRequest, DetectionResponse, FieldResult)
  detection.py          → classifier.py, models.py, db/orm.py
  routers/detect.py     → detection.py, models.py, classifier.py, config.py
  routers/logs.py       → db/orm.py, models.py, config.py
  main.py               → routers/detect.py, routers/logs.py, db/engine.py, classifier.py

injection-detector-dashboard/
  hooks/useLogs.ts      → api/client.ts, types/api.ts
  hooks/useLogStats.ts  → api/client.ts, types/api.ts
  hooks/useProbabilities.ts → api/client.ts, types/api.ts
  hooks/useEval.ts      → api/client.ts, types/api.ts
  DetectionLogTable.tsx → hooks/useLogs.ts, types/api.ts
  FieldAnalysisChart.tsx → hooks/useLogStats.ts, types/api.ts
  ConfidenceHistogram.tsx → hooks/useProbabilities.ts, types/api.ts
  ModelCard.tsx         → hooks/useEval.ts, types/api.ts
  App.tsx               → all four components
```

No circular dependencies. `models.py` has no internal imports. `db/orm.py` imports from `db/engine.py` only.

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Error handling (training) | Raise specific exceptions with context (`from exc`). `generate_negatives_batch` raises `RuntimeError` on Ollama unreachable. `load_negatives` raises `FileNotFoundError` if JSONL missing. Training CLI catches only at boundary (top-level lifespan context). |
| Error handling (service) | `run_detection` raises `RuntimeError` if classifier uninitialised. All DB failures propagate to FastAPI exception handlers (500). Proxy HTTP errors from downstream LLM return 502. No silent swallowing. |
| Configuration | pydantic-settings with `extra="ignore"` in both Python projects. Service settings injected via `Depends(get_settings)` — not imported directly in handlers. |
| Logging | Python `logging` with `logging.basicConfig(level=logging.INFO)`. Training CLI logs epoch progress via Trainer callbacks. Service logs every request at INFO level. All `except` blocks use `logger.error("...", exc_info=True)`. |
| Testing (training) | pytest. `load_spml` mocked with `monkeypatch`. `generate_negative` tested with `pytest-httpserver`. `compute_metrics` and `compute_calibration_bins` tested with fixed inputs — assert exact output. |
| Testing (service) | pytest + pytest-asyncio. Test DB via `TEST_DATABASE_URL`. Mock `Classifier` injected by overriding `get_classifier` dependency. Aggregation endpoints tested with seeded data (`test_logs_stats_with_seeded_data`). |
| Testing (dashboard) | vitest + @testing-library/react. API calls mocked via `msw`. Assert rendered text/badges, not implementation internals. |
| Imports | Deferred imports for `transformers`, `datasets`, `torch` inside function bodies (not at module level) — avoids slow startup penalty on CLI calls. |
| DB migrations | Alembic. Initial migration creates `detection_log` table and indexes. `alembic upgrade head` run before service start. |
| CORS | FastAPI `CORSMiddleware` configured to allow the dashboard origin (`http://localhost:5173`). Origin configurable via `ALLOWED_ORIGINS` env var. |
| Type hints | `from __future__ import annotations` in all Python files. All function signatures typed. `X | None` not `Optional[X]`. |

---

## Implementation Notes for Implementer

### Training Project

**SPML dataset field inspection (do first):**
Before writing `load_spml()`, run the inspection command from OQ1. The function must rename source columns to `"text"` and `"label"` regardless of what the source names are. Use `dataset.rename_columns({"prompt": "text"})` (or appropriate source name). Do not hardcode `"prompt"` in downstream code — normalise to `"text"` at load time.

**Synthetic negatives label alignment:**
Every row in `negatives.jsonl` has `"label": 0` (benign). Every row from SPML that is an injection has `"label": 1`. After `build_dataset()`, the combined dataset has balanced or near-balanced classes depending on SPML size. Log the class distribution after building the combined dataset.

**Trainer configuration — MPS gotchas:**
- Do not pass `no_cuda=True` or `bf16=True` — both fail on MPS in transformers 5.x.
- `warmup_steps` (integer, not `warmup_ratio`) — see python-conventions.md.
- `eval_strategy` and `save_strategy` must both be `"epoch"` (required when `load_best_model_at_end=True`).
- `accelerate` must be an explicit dependency in `pyproject.toml`.
- Batch size 64 is tested on 24GB M4 unified memory with DistilBERT. Do not reduce without testing.

**EvalResult serialisation:**
`dataclasses.asdict()` on `EvalResult` handles nested `CalibrationBin` dataclasses automatically. Output JSON keys match the field names (snake_case). The dashboard's `EvalResultSchema` Pydantic model mirrors these field names exactly.

**generate-negatives CLI — Ollama connection check:**
Before the generation loop, send a `GET /api/tags` request to the Ollama base URL. If it fails with `ConnectError`, raise `RuntimeError("Ollama is not running at {url}. Start Ollama before running generate-negatives.")` and exit. Do not attempt to call the model with a broken connection.

### Detection Service

**Classifier load path:**
`MODEL_CHECKPOINT_DIR` should point to the directory produced by `model.save_pretrained()` (contains `config.json`, `model.safetensors`, `tokenizer_config.json`). Validate `config.json` exists in the lifespan before loading. Use `AutoModelForSequenceClassification.from_pretrained(path)` and `AutoTokenizer.from_pretrained(path)`.

**predict_field inference:**
Tokenize with `padding=True, truncation=True, max_length=512, return_tensors="pt"`. Move inputs to the same device as the model. Run `model(**inputs)` inside `torch.no_grad()`. Softmax over `logits` dimension 1; return `float(probs[0][1])`.

**Proxy raw body passthrough:**
In the proxy handler, access the raw body via `await raw_request.body()` before parsing as `DetectionRequest`. Parse JSON manually: `request = DetectionRequest.model_validate_json(raw_body)`. Pass `raw_body` (bytes) to `httpx.AsyncClient.post()` as `content=raw_body`. Do not re-serialise the DetectionRequest — that would lose any extra fields the caller sent.

**JSONB field_results column:**
Store `[f.model_dump() for f in response.fields]`. The `field_name` in each element (`"tool_output_0"`, etc.) is the key used in the `field_flag_rates` aggregation query. No separate column per tool output — the JSONB array is the schema.

**GET /logs/stats field_flag_rates SQL:**
```sql
SELECT
    elem->>'field_name' AS field_name,
    AVG((elem->>'flagged')::boolean::int) AS flag_rate
FROM detection_log,
     jsonb_array_elements(field_results) AS elem
GROUP BY field_name
ORDER BY field_name
```
This unnests the JSONB array and computes flag rate per field across all log entries. The GIN index on `field_results` covers this query.

**Threshold env var:**
`INJECTION_THRESHOLD=0.7` is documented in `.env.example` with a comment: "Lower values = more sensitive (more false positives); higher = more specific. 0.7 is calibrated for precision >= recall on the SPML test set." The implementer must not hardcode 0.7 in source — always read from `settings.injection_threshold`.

### Dashboard

**Confidence histogram binning:**
Use `Math.min(Math.floor(p.probability * 10), 9)` to handle the edge case where `probability === 1.0` (would otherwise give index 10). This matches the calibration bin convention in the training project.

**FieldAnalysisChart — field name ordering:**
Sort by flag rate descending so the most dangerous fields appear first. This makes the chart readable without axis label truncation.

**DetectionLogTable — pagination:**
`total` from `LogsResponse` drives the page count: `Math.ceil(total / page_size)`. Render page buttons or prev/next controls. Do not fetch all records client-side and paginate in React — always pass `page` to the hook.

**ModelCard — calibration chart interpretation:**
When `mean_predicted_probability` matches `fraction_of_positives` in a bin, the model is well-calibrated. Add a comment in the component explaining this so the implementer doesn't remove the comparison. The visual is two bars of equal height = well-calibrated.

**`.env.example` for dashboard:**
```
VITE_API_BASE_URL=http://localhost:8000
```
Every `import.meta.env.VITE_*` reference must have a matching entry in `.env.example`.

---

## Handoff

Next role: implementer

The implementer reads this file and the planner output to produce working code for all three sub-projects: `injection-detector-training/`, `injection-detector/`, and `injection-detector-dashboard/`. All five open questions are resolved. No design decisions remain.

**Flags for implementer:**
1. **SPML field names — run the inspection before writing `load_spml()`** (OQ1 resolution above). Do not assume `"prompt"` without confirming.
2. **`accelerate` must be an explicit dep** in `injection-detector-training/pyproject.toml` — transformers Trainer requires it at runtime in 5.x.
3. **`warmup_steps` not `warmup_ratio`** — see python-conventions.md. `warmup_ratio` was removed in transformers 5.2.
4. **Proxy raw body** — do not re-serialise `DetectionRequest`; use `await raw_request.body()` and pass bytes to httpx.
5. **Aggregation test** — `test_logs_stats_with_seeded_data` must assert computed `field_flag_rates` values, not just response shape. Empty-DB tests do not verify SQL correctness.
6. **Alembic migration** — `alembic init` and initial migration are implementer deliverables. Service README documents `alembic upgrade head` as a setup step.
