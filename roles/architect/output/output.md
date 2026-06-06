# Architect Output — llm-safety-monitor

**Role:** architect
**Sequence:** `new-project-full` (step 3)
**Date:** 2026-06-06

---

## System Overview

The system has two distinct sub-projects. The **training project** (`llm-safety-monitor-training/`) is a standalone uv project with heavy ML dependencies that trains three DistilBERT classifiers — a pair safety classifier, a prompt adversarial detector, and a harm taxonomy classifier — and writes checkpoints to the shared `resources/models/` directory. The **streaming app** (`llm-safety-monitor/`) is the deployed system: a Kafka replay producer samples four LLM interaction datasets, three consumer threads each load a checkpoint and classify every event, an `EscalationPoller` daemon applies the 2×2 verdict matrix and posts actionable cases to case-queue, and a FastAPI service serves the five-tab React dashboard. Postgres stores two tables: `interactions` (event-level ground truth, one row per event) and `classifications` (prediction-level, one row per model per event). The API computes live F1 and calibration data by joining these tables against events with non-null ground truth labels.

---

## Data Models

### Training Project

```python
# llm_safety_training/datasets.py

@dataclass
class WildGuardSplits:
    pair_train_texts: list[str]
    pair_train_labels: list[int]          # binary: 0=safe, 1=unsafe
    pair_eval_texts: list[str]
    pair_eval_labels: list[int]
    taxonomy_train_texts: list[str]
    taxonomy_train_labels: list[list[int]] # 13-dim binary vectors, one per example
    taxonomy_eval_texts: list[str]
    taxonomy_eval_labels: list[list[int]]

@dataclass
class CalibrationBinData:
    bin_lower: float
    bin_upper: float
    count: int
    actual_positive_rate: float

@dataclass
class EvalResult:
    model_type: Literal["pair", "prompt", "taxonomy"]
    f1: float
    precision: float
    recall: float
    per_category_f1: dict[str, float] | None  # taxonomy only; None for binary
    calibration_bins: list[CalibrationBinData]
    sample_count: int
    timestamp: str  # ISO 8601
```

### Streaming App — Enums and Kafka Event

```python
# llm_safety_monitor/types.py

class SourceDataset(StrEnum):
    HH_RLHF = "hh-rlhf"
    WILDGUARD = "wildguard"
    ADVBENCH = "advbench"
    JAILBREAKBENCH = "jailbreakbench"
    LIVE = "live"

class HarmCategory(StrEnum):
    # Implementer: verify exact names from WildGuard dataset label schema before coding.
    # Approximate list based on WildGuard paper — actual column names in the dataset
    # must match exactly for label mapping to work correctly.
    HATE = "hate"
    HARASSMENT = "harassment"
    VIOLENCE = "violence"
    SELF_HARM = "self_harm"
    SEXUAL = "sexual"
    PRIVACY = "privacy"
    FINANCIAL_CRIME = "financial_crime"
    MALWARE = "malware"
    WEAPONS = "weapons"
    DRUGS = "drugs"
    MISINFORMATION = "misinformation"
    TERRORISM = "terrorism"
    OTHER = "other"

class EscalationReason(StrEnum):
    JAILBREAK = "JAILBREAK"
    BENIGN_HARMFUL = "BENIGN_HARMFUL"
    LOG_ONLY = "LOG_ONLY"
    MODEL_DISAGREEMENT = "MODEL_DISAGREEMENT"
    ADVERSARIAL_PROMPT_FLAGGED = "ADVERSARIAL_PROMPT_FLAGGED"

class LLMInteractionEvent(BaseModel):
    event_id: UUID
    prompt: str
    response: str | None
    source_dataset: SourceDataset
    ground_truth_safe: bool | None
    ground_truth_categories: list[HarmCategory] | None
```

### DB ORM — `llm_safety_monitor/api/models.py`

```python
class Interaction(Base):
    __tablename__ = "interactions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    prompt_text: Mapped[str]
    response_text: Mapped[str | None]
    source_dataset: Mapped[str]
    ground_truth_safe: Mapped[bool | None]
    ground_truth_categories: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    escalated: Mapped[bool] = mapped_column(default=False)
    escalation_reason: Mapped[str | None]  # EscalationReason value or None

class ClassificationResult(Base):
    __tablename__ = "classifications"
    # existing columns carried over:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    model_name: Mapped[str]
    content: Mapped[str]        # prompt text (truncated 500 chars) — kept for compat
    predicted_label: Mapped[int]
    confidence: Mapped[float]
    latency_ms: Mapped[float]
    processed_at: Mapped[datetime]
    seeded: Mapped[bool] = mapped_column(default=False)
    # new columns (added via migration):
    event_id: Mapped[UUID | None] = mapped_column(ForeignKey("interactions.id"), index=True)
    taxonomy_labels: Mapped[list | None] = mapped_column(JSONB)
```

**`predicted_label` and `confidence` conventions per model:**

| Model | `predicted_label` | `confidence` | `taxonomy_labels` |
|-------|-------------------|--------------|-------------------|
| `pair_classifier` | 0=safe, 1=unsafe | P(unsafe) | NULL |
| `prompt_detector` | 0=benign, 1=adversarial | P(adversarial) | NULL |
| `taxonomy_classifier` | 1 if ≥1 category flagged, else 0 | max sigmoid across 13 heads | JSON list of active HarmCategory strings |

**Label alignment with `ground_truth_safe`:** `ground_truth_safe=True` → label 0; `ground_truth_safe=False` → label 1. The metrics router converts `ground_truth_safe` to `1 - int(ground_truth_safe)` before computing F1 against `predicted_label`.

### API Schemas — `llm_safety_monitor/api/schemas.py`

```python
class VerdictEntry(BaseModel):
    model_name: str
    predicted_label: int
    confidence: float
    taxonomy_labels: list[str] | None  # populated for taxonomy_classifier only

class RecentEvent(BaseModel):
    event_id: UUID
    prompt_text: str          # truncated to 200 chars
    response_text: str | None # truncated to 200 chars
    source_dataset: str
    verdicts: list[VerdictEntry]
    escalation_reason: str | None

class StreamResponse(BaseModel):
    events: list[RecentEvent]

class ModelMetrics(BaseModel):
    model_name: str
    f1: float
    precision: float
    recall: float
    sample_count: int

class MetricsResponse(BaseModel):
    models: list[ModelMetrics]

class CalibrationBin(BaseModel):
    bin_lower: float
    bin_upper: float
    count: int
    actual_positive_rate: float

class ModelCalibration(BaseModel):
    model_name: str
    bins: list[CalibrationBin]  # only bins with count > 0

class CalibrationResponse(BaseModel):
    models: list[ModelCalibration]

# DisagreementsResponse carried over from existing implementation
```

### Frontend Types — `web/src/types/index.ts`

```typescript
type SourceDataset = 'hh-rlhf' | 'wildguard' | 'advbench' | 'jailbreakbench' | 'live'

type EscalationReason =
  | 'JAILBREAK'
  | 'BENIGN_HARMFUL'
  | 'LOG_ONLY'
  | 'MODEL_DISAGREEMENT'
  | 'ADVERSARIAL_PROMPT_FLAGGED'

type VerdictEntry = {
  model_name: string
  predicted_label: number
  confidence: number
  taxonomy_labels: string[] | null
}

type RecentEvent = {
  event_id: string
  prompt_text: string
  response_text: string | null
  source_dataset: SourceDataset
  verdicts: VerdictEntry[]
  escalation_reason: EscalationReason | null
}

type StreamResponse = { events: RecentEvent[] }

type ModelMetrics = {
  model_name: string
  f1: number
  precision: number
  recall: number
  sample_count: number
}

type MetricsResponse = { models: ModelMetrics[] }

type CalibrationBin = {
  bin_lower: number
  bin_upper: number
  count: number
  actual_positive_rate: number
}

type ModelCalibration = {
  model_name: string
  bins: CalibrationBin[]
}

type CalibrationResponse = { models: ModelCalibration[] }
```

---

## Module Interfaces

### `llm_safety_training/datasets.py`

```python
def extract_hhrlhf_pair(field: str) -> str:
    """Extract 'final human turn [SEP] final assistant turn' from a HH-RLHF chosen/rejected string."""

def load_hhrlhf_binary(split: str = "train") -> tuple[list[str], list[int]]:
    """Returns (texts, labels) where text = extract_hhrlhf_pair(chosen|rejected), label=0/1."""

def split_wildguard(seed: int = 42) -> WildGuardSplits:
    """70/30 example-level split. Each allocation's 10% reserve becomes the eval set."""

def load_advbench() -> tuple[list[str], list[int]]:
    """All AdvBench harmful instructions; label=1 for all."""

def load_jailbreakbench() -> tuple[list[str], list[int]]:
    """All JailbreakBench prompt variants; label=1 for all."""

def build_prompt_detector_dataset(seed: int = 42) -> tuple[list[str], list[int], list[str], list[int]]:
    """Returns (train_texts, train_labels, eval_texts, eval_labels).
    Positives: AdvBench + JailbreakBench + WildGuard harmful (subset).
    Negatives: HH-RLHF chosen prompts + WildGuard safe prompts. Balanced 50/50."""
```

### `llm_safety_training/train_pair.py`

Entry point: `uv run train-pair`

```python
def train(
    output_dir: Path,
    epochs: int = 4,
    batch_size: int = 128,
    seed: int = 42,
) -> None:
    """Trains DistilBERT binary classifier on HH-RLHF + WildGuard pair split.
    Saves checkpoint to output_dir. Uses Trainer with eval_strategy='epoch',
    save_strategy='epoch', load_best_model_at_end=True, warmup_steps (not warmup_ratio)."""
```

### `llm_safety_training/train_taxonomy.py`

Entry point: `uv run train-taxonomy`

```python
def train(
    output_dir: Path,
    epochs: int = 4,
    batch_size: int = 64,  # 13-head model; reduce from 128 if OOM
    seed: int = 42,
) -> None:
    """Multi-label DistilBERT. Custom Trainer subclass overrides compute_loss to use
    BCEWithLogitsLoss. Threshold 0.5 per category for predicted labels."""
```

### `llm_safety_training/evaluate.py`

Entry point: `uv run evaluate --model pair|prompt|taxonomy`

```python
def evaluate(
    model_type: Literal["pair", "prompt", "taxonomy"],
    checkpoint_path: Path,
    output_dir: Path,
) -> EvalResult:
    """Loads checkpoint, runs on held-out split, computes metrics, writes JSON.
    For taxonomy: per-category F1 via sklearn multilabel_confusion_matrix.
    For all: calibration bins computed with 10 equal-width bins over confidence scores."""

def write_eval_json(result: EvalResult, output_path: Path) -> None: ...
```

### `llm_safety_monitor/producer.py`

Entry point: `uv run producer`

```python
class ReplayProducer:
    def __init__(self, settings: Settings) -> None:
        # Loads all 4 datasets into memory. Shuffles each per-dataset (random seed each run).
        # Wraps each in itertools.cycle. Computes weights from REPLAY_MIX_* settings.
        ...

    def run(self) -> None:
        """Blocking loop. Each tick: random.choices over 4 cycled iterators using mix weights.
        Serialises LLMInteractionEvent to JSON, writes to interactions table (sync SQLAlchemy),
        publishes to Kafka, sleeps ~3 seconds."""

    def _write_interaction(self, event: LLMInteractionEvent, session: Session) -> None:
        """Inserts into interactions table. Called before Kafka publish."""
```

### `llm_safety_monitor/consumers/base.py`

```python
class ClassifyResult(TypedDict):
    predicted_label: int
    confidence: float
    latency_ms: float
    taxonomy_labels: list[str] | None

class BaseConsumer:
    model_name: str  # "pair_classifier" | "prompt_detector" | "taxonomy_classifier"

    def __init__(self, mode: Literal["production", "shadow"], model_name: str) -> None:
        """Loads model checkpoint from settings. Raises RuntimeError if path absent."""

    def classify(self, text: str) -> ClassifyResult:
        """Subclasses implement. text = prompt [SEP] response for pair/taxonomy, prompt only for detector."""

    def _write_classification(self, event_id: UUID, result: ClassifyResult, session: Session) -> None:
        """Inserts into classifications table."""

    def run(self) -> None:
        """Blocking Kafka poll loop. For each message: classify, write to DB. Catches exceptions
        per message with logger.warning(exc_info=True); does not crash the loop."""

    def stop(self) -> None: ...
```

### `llm_safety_monitor/consumers/taxonomy_classifier.py`

Subclasses `BaseConsumer`. Override `classify`:
- Sigmoid over all 13 logits → per-category probabilities
- `taxonomy_labels` = list of `HarmCategory` values where probability > 0.5
- `predicted_label` = 1 if len(taxonomy_labels) > 0, else 0
- `confidence` = max probability across all 13 heads (0.0 if all < 0.5 and predicted_label=0, else the max)

### `llm_safety_monitor/consumers/runner.py`

```python
def run_all(settings: Settings) -> None:
    """Starts pair_classifier, prompt_detector, taxonomy_classifier, and EscalationPoller
    as daemon threads. Blocks until KeyboardInterrupt. Calls stop() on each on exit."""
```

### `llm_safety_monitor/escalation/router.py`

```python
class EscalationPoller:
    """Daemon thread. Polls every 2 seconds for events where all 3 classification rows
    exist and escalated=False. Applies 2×2 matrix. Also handles timeout: events older
    than 10 seconds with escalated=False and fewer than 3 classification rows are
    marked escalated=True with no case-queue post and a warning log."""

    def __init__(self, settings: Settings) -> None: ...
    def run(self) -> None: ...
    def stop(self) -> None: ...

def compute_escalation_reason(
    pair_label: int,
    pair_conf: float,
    prompt_label: int,
    prompt_conf: float,
    taxonomy_labels: list[str],
    has_response: bool,
) -> EscalationReason | None:
    """Pure function. Returns EscalationReason or None (no action needed).
    Matrix:
      has_response=False, prompt_label=1, prompt_conf>0.7 → ADVERSARIAL_PROMPT_FLAGGED
      pair=1, prompt=1 → JAILBREAK
      pair=1, prompt=0 → BENIGN_HARMFUL
      pair=0, prompt=1 → LOG_ONLY (no case-queue post)
      pair=0, taxonomy non-empty → MODEL_DISAGREEMENT
      pair=1, taxonomy empty → MODEL_DISAGREEMENT
      else → None"""
```

**Escalation polling query (conceptual):**

```sql
-- Ready events: all 3 classification rows present
SELECT i.id FROM interactions i
WHERE i.escalated = FALSE
  AND EXISTS (SELECT 1 FROM classifications c WHERE c.event_id=i.id AND c.model_name='pair_classifier')
  AND EXISTS (SELECT 1 FROM classifications c WHERE c.event_id=i.id AND c.model_name='prompt_detector')
  AND EXISTS (SELECT 1 FROM classifications c WHERE c.event_id=i.id AND c.model_name='taxonomy_classifier')
LIMIT 100;

-- Timed-out events: stale without all 3 rows
SELECT i.id FROM interactions i
WHERE i.escalated = FALSE
  AND i.created_at < NOW() - INTERVAL '10 seconds'
  AND (
    NOT EXISTS (SELECT 1 FROM classifications c WHERE c.event_id=i.id AND c.model_name='pair_classifier')
    OR NOT EXISTS (SELECT 1 FROM classifications c WHERE c.event_id=i.id AND c.model_name='prompt_detector')
    OR NOT EXISTS (SELECT 1 FROM classifications c WHERE c.event_id=i.id AND c.model_name='taxonomy_classifier')
  )
LIMIT 100;
```

### API Routers

**`/metrics` (GET)**
```
Fetches (model_name, predicted_label, ground_truth_safe) for all classifications joined to
interactions where ground_truth_safe IS NOT NULL. Computes F1, precision, recall per model
using sklearn in Python. ground_truth_safe=True → y_true=0; False → y_true=1.
Returns MetricsResponse.
```

**`/metrics/calibration` (GET)**
```
Fetches (model_name, confidence, ground_truth_safe) from same join.
Bins confidence [0,1] into 10 equal-width buckets. Computes actual_positive_rate per bin.
Returns CalibrationResponse (bins with count=0 excluded).
```

**`/stream/recent` (GET, ?limit=50)**
```
Two queries:
  1. SELECT * FROM interactions ORDER BY created_at DESC LIMIT $limit
  2. SELECT * FROM classifications WHERE event_id = ANY($event_ids)
Merges in Python: group classifications by event_id, attach to each interaction as verdicts.
Truncates prompt_text and response_text to 200 chars before returning.
Returns StreamResponse.
```

**`/metrics/disagreements` (GET)** — carried over, no changes.

### Frontend Hooks

```typescript
// api/stream.ts
function useRecentEvents(limit = 50): QueryResult<StreamResponse>
// polls every 5s via TanStack Query refetchInterval

// api/metrics.ts
function useModelMetrics(): QueryResult<MetricsResponse>
// polls every 30s

function useCalibration(): QueryResult<CalibrationResponse>
// polls every 60s (changes slowly)

function useDisagreements(): QueryResult<DisagreementsResponse>
// polls every 30s — carried over

// api/review.ts
function useEscalationQueue(): QueryResult<EscalationQueueResponse>
function useDecide(eventId: string): MutationResult<void>
```

### Frontend Components

**`VerdictRow.tsx`**
```typescript
function VerdictRow({ verdicts }: { verdicts: VerdictEntry[] }): JSX.Element
// 3-column layout: pair verdict (Safe|Unsafe badge), prompt verdict (Benign|Adversarial badge),
// taxonomy verdict (list of HarmCategory chips or "none" text).
// Takes verdicts array; finds each model by model_name.
```

**`SourceBadge.tsx`**
```typescript
function SourceBadge({ source }: { source: SourceDataset }): JSX.Element
// Colour-coded badge: hh-rlhf=blue, wildguard=purple, advbench=red, jailbreakbench=orange, live=green
```

**`CalibrationChart.tsx`**
```typescript
function CalibrationChart({ data }: { data: ModelCalibration }): JSX.Element
// recharts LineChart.
// X axis: bin_lower (0–1, labeled as percentages). Y axis: actual_positive_rate (0–1).
// Two series: actual (dots+line from data) and perfect calibration (diagonal y=x reference line).
// ReferenceLine at slope 1 via recharts ReferenceLine.
```

**`EscalationReasonBadge.tsx`**
```typescript
function EscalationReasonBadge({ reason }: { reason: EscalationReason | null }): JSX.Element
// Null → renders nothing. Colour scheme:
// JAILBREAK=red, BENIGN_HARMFUL=orange, MODEL_DISAGREEMENT=yellow,
// ADVERSARIAL_PROMPT_FLAGGED=purple, LOG_ONLY=gray
```

---

## Dependencies

```
llm-safety-monitor-training/ (standalone, no runtime deps on streaming app)
  llm_safety_training/datasets.py
    ← no internal deps
  llm_safety_training/train_pair.py, train_prompt.py, train_taxonomy.py
    ← datasets.py
  llm_safety_training/evaluate.py
    ← datasets.py (for held-out splits)

llm-safety-monitor/ (streaming app)
  config.py ← no internal deps
  types.py  ← no internal deps
  api/models.py ← types.py
  api/schemas.py ← types.py
  api/database.py ← config.py
  api/routers/* ← models.py, schemas.py, database.py
  api/main.py ← routers/*, database.py
  consumers/base.py ← config.py, types.py, api/models.py (sync engine)
  consumers/pair_classifier.py ← base.py
  consumers/prompt_detector.py ← base.py
  consumers/taxonomy_classifier.py ← base.py, types.py (HarmCategory)
  consumers/runner.py ← all consumers, escalation/router.py
  escalation/router.py ← config.py, types.py, api/models.py (sync engine)
  producer.py ← config.py, types.py, api/models.py (sync engine)

  web/ (frontend — depends on API contract only, not Python code)
  types/index.ts ← no internal deps
  api/client.ts ← no internal deps
  api/stream.ts, metrics.ts, review.ts ← client.ts, types/index.ts
  components/* ← types/index.ts
  pages/* ← api hooks, components, types/index.ts
```

**Two SQLAlchemy engines:** consumers, producer, and EscalationPoller use a **synchronous** engine (blocking Kafka loops). The API uses an **async** engine (FastAPI lifespan). Both target the same Postgres database. This is the same pattern as moderation-dashboard — no shared sessions between them.

No circular dependencies.

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Error handling | Specific exceptions with context (`raise RuntimeError(...) from exc`). Consumer loops catch per-message exceptions with `logger.warning(exc_info=True)`, do not crash the loop. Missing checkpoint raises `RuntimeError` at startup — fail loud, not silent. |
| Configuration | `pydantic-settings` `Settings` class with `extra="ignore"`. Single `.env` file. Consumers, producer, and EscalationPoller all instantiate `Settings()` at startup. |
| Logging | `logging` stdlib. Root logger configured in `main.py` and `runner.py` at `INFO` level. Per-module loggers via `logger = logging.getLogger(__name__)`. All exception boundaries log with `exc_info=True`. |
| DB engines | Two engines: `create_async_engine` for FastAPI; `create_engine` (sync) for consumers + producer + poller. Neither shares sessions across thread/coroutine boundaries. |
| Testing (training) | Patch `transformers.AutoModelForSequenceClassification.from_pretrained` (source) and `Trainer.train`, `Trainer.save_model`. Do not patch module-level names (deferred imports per python-conventions.md). |
| Testing (API) | Real async test DB (sqlite or postgres). `conftest.py` seeds interactions + classifications. Assert computed output values, not just shape. |
| Testing (consumers) | Mock the HuggingFace pipeline object. Verify label, confidence in [0,1], latency > 0. |
| Testing (frontend) | msw for API mocks. Test behaviour (rendered text, badges) not internal state. |
| Type hints | All function signatures annotated. `from __future__ import annotations` at top of every Python file. |

---

## Implementation Notes for Implementer

**Training order matters:**
- `datasets.py` must be complete before any `train_*.py` — all three share it.
- WildGuard 70/30 split must use the same seed=42 so `train_pair.py` and `train_taxonomy.py` get non-overlapping examples every time.
- The `build_prompt_detector_dataset` function draws WildGuard positives from the 70% pair allocation (not an independent draw) to ensure the taxonomy's 30% is not contaminated.

**HH-RLHF parsing:**
The `chosen` and `rejected` fields look like: `"\n\nHuman: ...\n\nAssistant: ..."`. Parse by splitting on `"\n\nHuman: "` and `"\n\nAssistant: "`. The last Human segment + last Assistant segment form the pair. Strip whitespace. If parsing fails (malformed string), skip the example and log a warning — do not crash.

**Taxonomy multi-label Trainer:**
Standard `AutoModelForSequenceClassification` with `num_labels=13` and `problem_type="multi_label_classification"` automatically uses `BCEWithLogitsLoss` — no custom Trainer subclass needed. Set `model.config.problem_type = "multi_label_classification"` before training. Labels must be `float` tensors (not `long`) for BCEWithLogitsLoss.

**WildGuard harm category names:**
Load the dataset with `datasets.load_dataset("allenai/wildguard")` and inspect the feature schema to get the exact column names for the 13 harm categories. The `HarmCategory` StrEnum values must match these names exactly — the implementer must update the enum after inspecting the schema. Do not hardcode approximate names.

**EscalationPoller sync engine:**
The poller runs in a daemon thread alongside the consumers. Use `sessionmaker(bind=sync_engine)` and create a new session per poll cycle (`with Session() as session:`). Do not share sessions across cycles.

**`LOG_ONLY` escalation reason:**
`LOG_ONLY` (adversarial prompt + safe response) does not POST to case-queue. The poller logs it at `INFO` level and marks `escalated=TRUE` with `escalation_reason="LOG_ONLY"`. The stream endpoint returns it so the dashboard can display it, but no human review queue entry is created.

**`/stream/recent` truncation:**
Truncate `prompt_text` and `response_text` to 200 chars with `text[:200]` (no ellipsis needed — the frontend displays as-is).

**CalibrationChart reference line:**
recharts does not natively draw a y=x diagonal. Use a `ReferenceLine` with a custom `segment` prop: `segment={[{x: 0, y: 0}, {x: 1, y: 1}]}`. This draws the perfect calibration diagonal. Requires recharts ≥ 2.5.

**Postgres port:**
Use port 5434 for this project (5432 reserved for case-queue, 5433 for moderation-stream/moderation-dashboard). Document in `docker-compose.yml` and `.env.example`.

**`taxonomy_labels` in `classifications`:**
Store as a JSON array of strings matching `HarmCategory` values: `["hate", "violence"]`. Empty list `[]` means the taxonomy classifier ran but flagged no categories. `NULL` means the row belongs to a non-taxonomy model (pair or prompt).

**Frontend `CalibrationChart` test:**
recharts renders SVG — `@testing-library/react` assertions should check for rendered axis labels or the component's container (not SVG path data). The test should verify the component renders without crashing when passed a `ModelCalibration` prop and that the model name appears in the DOM.

---

## Resolutions to Planner Open Questions

1. **Calibration schema:** Confirmed. `{models: [{model_name, bins: [{bin_lower, bin_upper, count, actual_positive_rate}]}]}`. Zero-count bins excluded. `actual_positive_rate` omitted (not present in object) when excluded — no null, just not in the list.

2. **Taxonomy categories StrEnum:** Confirmed as `StrEnum` in `types.py`. Names must be verified from dataset schema at implementation time. Approximate 13 provided above as a starting template — implementer replaces with actual names.

3. **Escalation coordination:** Changed from DB-poll-per-write to a dedicated `EscalationPoller` daemon thread (polls every 2s). Cleaner than per-consumer coordination, no cross-thread locking needed. Adds `escalated BOOLEAN DEFAULT FALSE` and `escalation_reason VARCHAR NULLABLE` to `interactions` table.

4. **Replay producer in-memory state:** Confirmed. In-memory shuffle + `itertools.cycle`. Memory safe: ~262k items × ~600 bytes avg ≈ 160MB. Weighted sampling via `random.choices(population=[iter_a, iter_b, iter_c, iter_d], weights=[0.60, 0.25, 0.10, 0.05])`.

5. **Taxonomy consumer output format:** Confirmed compact representation. `predicted_label=1|0`, `confidence=max sigmoid`, `taxonomy_labels=["hate", ...]` stored as JSONB on `classifications`. `classifications.taxonomy_labels` column is JSONB NULLABLE.

---

## Handoff

Next role: implementer

Reads: this file (`roles/architect/output/output.md`) + `roles/planner/output/output.md`.

**Implement in this order:**
1. `llm-safety-monitor-training/`: `datasets.py` → `train_pair.py` + `train_prompt.py` + `train_taxonomy.py` (parallel) → `evaluate.py` → tests
2. `llm-safety-monitor/` DB + config: Alembic migration → `config.py` → `types.py`
3. `producer.py` + its test
4. Consumers: `base.py` → `pair_classifier.py` + `prompt_detector.py` + `taxonomy_classifier.py` (parallel) → `runner.py`
5. `escalation/router.py` + its test
6. API: `models.py` → `schemas.py` → routers → `main.py` + tests
7. Frontend: `types/index.ts` → api hooks → components → pages + tests

**Uncertain interfaces:** The exact WildGuard harm category names are uncertain until the dataset is inspected. The `HarmCategory` StrEnum and any code depending on it (taxonomy classifier label mapping, DB values, frontend type) must be finalized from the dataset schema before training runs. Everything else is fully specified.
