# Architect Output — cai-preference-trainer

**Role:** architect
**Sequence:** `new-project-full` (step 3)
**Date:** 2026-06-06

---

## System Overview

`cai-preference-trainer` is a three-process system: a FastAPI backend (`cai-preference-trainer-api/`), a standalone training CLI (`cai-preference-trainer/`), and a React SPA (`cai-preference-trainer-ui/`). The API owns the Postgres database (port 5436) and exposes all read/write endpoints. The frontend is a 4-tab dashboard plus an `/annotate` route — both in the same SPA. The training CLI connects directly to the same Postgres DB (read-only) to build its training dataset, then writes a checkpoint to `resources/models/cai-preference-trainer/` and an eval JSON to `resources/evals/cai-preference-trainer/`. The API reads the latest eval JSON file to serve calibration and RM eval tabs — it does not call the trainer. The Ollama pair generator (`scripts/generate_pairs.py`) is a separate CLI script that calls the API's ingest endpoint, keeping pair storage centralised. The 10 CAI principles are a Python module constant in the API (`principles.py`) and a JSON sidecar file (`principles.json`) used by the frontend for display — no DB table, no admin UI.

Data flow: Ollama CLI / HH-RLHF ingestor → `response_pairs` → annotation UI → `annotations` → training CLI → checkpoint + eval JSON → dashboard.

---

## Open Questions Resolved

**OQ1 — DB connection from trainer:**
Direct Postgres connection via SQLAlchemy (synchronous, not async — the trainer is a batch CLI, not a web server). The trainer's `.env` contains `DB_URL` pointing to the same Postgres instance. The trainer uses a read-only SQLAlchemy session; it never writes to `response_pairs` or `annotations`.

**OQ2 — Calibration data source:**
Computed at eval time by `evaluate-rm` CLI, stored in the eval JSON alongside accuracy/AUC. The API reads the latest JSON file (`eval_loader.py`) and serves the pre-computed bins. The API does not recompute calibration from raw predictions. This keeps the API stateless with respect to ML artifacts.

**OQ3 — Annotator ID flow:**
`annotator_id` is stored in `localStorage` under key `cai_annotator_id`. On first visit to `/annotate`, if `localStorage` is empty, the UI renders a one-field name prompt modal before showing the annotation queue. Once set, it persists across sessions. The queue API receives `annotator_id` as a query parameter. No separate settings page needed.

**OQ4 — Queue response shape for partial annotations:**
`GET /api/pairs/queue` returns `QueueItem` objects. Each `QueueItem` includes `rated_principle_count: int` (0–10 for this annotator) so the frontend can show "Resume (N/10)" vs "Start". The API computes this via a subquery grouping `annotations` by `pair_id` and `annotator_id`. Full shape defined in Data Models.

**OQ5 — Principles static resource format:**
Python module constant in `cai_api/principles.py` (list of dicts with `id` and `text`). Same data duplicated to `cai-preference-trainer-ui/src/principles.json` for frontend display. No DB table. The trainer imports from its own copy: `cai_trainer/principles.py` (identical content). Single source of truth is the Python constant; frontend JSON is a copy maintained manually if principles ever change (they won't in v1).

---

## Data Models

### PostgreSQL Schema

```sql
-- Postgres port 5436
-- Applied via: alembic upgrade head

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TYPE pair_source AS ENUM ('hhrlhf', 'generated');
CREATE TYPE preferred_choice AS ENUM ('A', 'B', 'TIE');

CREATE TABLE response_pairs (
    pair_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt          TEXT NOT NULL,
    response_a      TEXT NOT NULL,
    response_b      TEXT NOT NULL,
    source          pair_source NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_response_pairs_source ON response_pairs (source);
CREATE INDEX idx_response_pairs_created_at ON response_pairs (created_at);

CREATE TABLE annotations (
    annotation_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pair_id         UUID NOT NULL REFERENCES response_pairs(pair_id) ON DELETE CASCADE,
    principle_id    INT NOT NULL CHECK (principle_id BETWEEN 1 AND 10),
    annotator_id    TEXT NOT NULL,
    preferred       preferred_choice NOT NULL,
    confidence      INT CHECK (confidence BETWEEN 1 AND 3),  -- nullable; NULL = not provided
    annotated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (pair_id, principle_id, annotator_id)  -- one rating per annotator per principle per pair
);

CREATE INDEX idx_annotations_pair_id ON annotations (pair_id);
CREATE INDEX idx_annotations_annotator_id ON annotations (annotator_id);
CREATE INDEX idx_annotations_principle_id ON annotations (principle_id);
-- Composite index for queue query (annotator's ratings per pair)
CREATE INDEX idx_annotations_pair_annotator ON annotations (pair_id, annotator_id);
```

### SQLAlchemy ORM Models

**`cai_api/models/response_pair.py`**

```python
from __future__ import annotations
import enum
import uuid
from datetime import UTC, datetime
from sqlalchemy import Enum as SAEnum, Index, String, Text
from sqlalchemy.dialects.postgresql import TIMESTAMPTZ, UUID
from sqlalchemy.orm import Mapped, mapped_column
from cai_api.database import Base


class PairSource(str, enum.Enum):
    hhrlhf = "hhrlhf"
    generated = "generated"


class ResponsePair(Base):
    __tablename__ = "response_pairs"

    pair_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response_a: Mapped[str] = mapped_column(Text, nullable=False)
    response_b: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[PairSource] = mapped_column(
        SAEnum(PairSource, name="pair_source"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, nullable=False, default=lambda: datetime.now(UTC)
    )
```

**`cai_api/models/annotation.py`**

```python
from __future__ import annotations
import enum
import uuid
from datetime import UTC, datetime
from sqlalchemy import CheckConstraint, Enum as SAEnum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMPTZ, UUID
from sqlalchemy.orm import Mapped, mapped_column
from cai_api.database import Base


class PreferredChoice(str, enum.Enum):
    A = "A"
    B = "B"
    TIE = "TIE"


class Annotation(Base):
    __tablename__ = "annotations"
    __table_args__ = (
        UniqueConstraint("pair_id", "principle_id", "annotator_id", name="uq_annotation"),
        CheckConstraint("principle_id BETWEEN 1 AND 10", name="ck_principle_range"),
        CheckConstraint("confidence BETWEEN 1 AND 3", name="ck_confidence_range"),
    )

    annotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pair_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("response_pairs.pair_id", ondelete="CASCADE"),
        nullable=False,
    )
    principle_id: Mapped[int] = mapped_column(Integer, nullable=False)
    annotator_id: Mapped[str] = mapped_column(String, nullable=False)
    preferred: Mapped[PreferredChoice] = mapped_column(
        SAEnum(PreferredChoice, name="preferred_choice"), nullable=False
    )
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    annotated_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, nullable=False, default=lambda: datetime.now(UTC)
    )
```

### Pydantic Schemas

**`cai_api/schemas/pair.py`**

```python
from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel
from cai_api.models.response_pair import PairSource


class QueueItem(BaseModel):
    pair_id: uuid.UUID
    prompt: str  # truncated to 200 chars for list display
    source: PairSource
    created_at: datetime
    rated_principle_count: int  # 0–10 for requesting annotator

    model_config = {"from_attributes": True}


class QueueResponse(BaseModel):
    items: list[QueueItem]
    total: int
    limit: int
    offset: int


class ResponsePairOut(BaseModel):
    pair_id: uuid.UUID
    prompt: str
    response_a: str
    response_b: str
    source: PairSource
    created_at: datetime

    model_config = {"from_attributes": True}


class IngestHHRLHFRequest(BaseModel):
    limit: int = 500  # number of pairs to ingest; default 500
    split: str = "train"  # HuggingFace dataset split


class IngestResponse(BaseModel):
    inserted: int
    skipped: int  # duplicates
```

**`cai_api/schemas/annotation.py`**

```python
from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from cai_api.models.annotation import PreferredChoice


class PrincipleRating(BaseModel):
    principle_id: int = Field(ge=1, le=10)
    preferred: PreferredChoice
    confidence: int | None = Field(default=None, ge=1, le=3)


class AnnotationBatch(BaseModel):
    pair_id: uuid.UUID
    annotator_id: str
    ratings: list[PrincipleRating] = Field(min_length=1, max_length=10)


class AnnotationOut(BaseModel):
    annotation_id: uuid.UUID
    pair_id: uuid.UUID
    principle_id: int
    annotator_id: str
    preferred: PreferredChoice
    confidence: int | None
    annotated_at: datetime

    model_config = {"from_attributes": True}


class AnnotationBatchResponse(BaseModel):
    created: list[AnnotationOut]
```

**`cai_api/schemas/stats.py`**

```python
from __future__ import annotations
from pydantic import BaseModel


class PrincipleCoverageItem(BaseModel):
    principle_id: int
    principle_text: str
    annotation_count: int
    agreement_rate: float  # fraction of non-TIE annotations (0.0–1.0)


class PrincipleCoverageResponse(BaseModel):
    principles: list[PrincipleCoverageItem]  # always 10 items


class PrincipleEvalResult(BaseModel):
    principle_id: int
    principle_text: str
    accuracy: float
    auc_roc: float
    n_eval_samples: int


class RMEvalResponse(BaseModel):
    checkpoint_dir: str
    trained_at: str  # ISO timestamp
    total_train_samples: int
    total_eval_samples: int
    per_principle: list[PrincipleEvalResult]  # 10 items


class CalibrationBin(BaseModel):
    bin_lower: float
    bin_upper: float
    predicted_prob_mean: float
    fraction_positive: float
    count: int


class PrincipleCalibration(BaseModel):
    principle_id: int
    bins: list[CalibrationBin]  # 10 bins


class CalibrationResponse(BaseModel):
    principles: list[PrincipleCalibration]  # up to 10; absent if no eval yet
```

### Principles Static Resource

**`cai_api/principles.py`** (identical copy in `cai_trainer/principles.py`)

```python
from __future__ import annotations

PRINCIPLES: list[dict[str, int | str]] = [
    {"id": 1, "text": "Choose the response that is most helpful, accurate, and avoids harm"},
    {"id": 2, "text": "Choose the response that is least likely to contain false information"},
    {"id": 3, "text": "Choose the response that a thoughtful Anthropic employee would prefer"},
    {"id": 4, "text": "Choose the response that is less harmful to the user or others"},
    {"id": 5, "text": "Choose the response that better respects personal autonomy"},
    {"id": 6, "text": "Choose the response that better follows safe messaging guidelines"},
    {"id": 7, "text": "Choose the response that is more honest and avoids deception"},
    {"id": 8, "text": "Choose the response that is less likely to be misused"},
    {"id": 9, "text": "Choose the response that better expresses uncertainty when appropriate"},
    {"id": 10, "text": "Choose the response that is more respectful and considerate"},
]

PRINCIPLE_MAP: dict[int, str] = {p["id"]: p["text"] for p in PRINCIPLES}
```

---

## Module Interfaces

### `cai_api/services/hhrlhf_ingestor.py`

```python
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from cai_api.schemas.pair import IngestResponse


async def ingest_hhrlhf(
    session: AsyncSession,
    limit: int,
    split: str,
) -> IngestResponse:
    """
    Load up to `limit` rows from Anthropic/hh-rlhf HuggingFace dataset (given split).
    Extract (prompt, response_a, response_b) via _parse_hhrlhf_row().
    Insert into response_pairs with source='hhrlhf'; skip on UniqueConstraint violation.
    Returns count of inserted and skipped rows.
    """
    ...


def _parse_hhrlhf_row(row: dict) -> tuple[str, str, str]:
    """
    Extract (prompt, response_a, response_b) from a HH-RLHF row.
    row["chosen"] format: "\n\nHuman: <prompt>\n\nAssistant: <response_a>"
    row["rejected"] format: "\n\nHuman: <prompt>\n\nAssistant: <response_b>"
    Split on "\n\nAssistant: " — take last segment as response.
    Extract prompt from Human: segment of chosen field.
    Returns (prompt, chosen_response, rejected_response).
    Raises ValueError if the format does not match expected structure.
    """
    ...
```

### `cai_api/services/calibration.py`

```python
from __future__ import annotations
from cai_api.schemas.stats import CalibrationBin


def compute_calibration_bins(
    predicted_probs: list[float],
    labels: list[int],
    n_bins: int = 10,
) -> list[CalibrationBin]:
    """
    Compute equal-width calibration bins.
    predicted_probs: model output probabilities for class 1 (B preferred).
    labels: ground truth (0=A preferred, 1=B preferred).
    n_bins: number of equal-width bins (default 10).
    Each bin: [lower, upper), mean predicted prob, fraction positive, count.
    Empty bins are included with count=0 and NaN values set to 0.0.
    Same logic as llm-safety-monitor calibration.
    """
    ...
```

### `cai_api/services/eval_loader.py`

```python
from __future__ import annotations
from pathlib import Path
from cai_api.schemas.stats import RMEvalResponse


def load_latest_eval(evals_dir: Path) -> RMEvalResponse | None:
    """
    Scan evals_dir for JSON files matching pattern cai-preference-trainer-*.json.
    Return the parsed RMEvalResponse from the most recently modified file.
    Returns None if no eval files exist.
    Raises ValueError if the file cannot be parsed as RMEvalResponse.
    """
    ...
```

### `cai_api/routers/pairs.py`

```python
# All endpoints are async. DB session injected via FastAPI Depends.

GET  /api/pairs/queue
    params: annotator_id: str, limit: int = 20, offset: int = 0
    response: QueueResponse
    # Subquery: count annotations WHERE annotator_id = :annotator_id GROUP BY pair_id
    # LEFT JOIN to get rated_principle_count per pair
    # Filter: rated_principle_count < 10 (partially or fully unannotated)
    # ORDER BY response_pairs.created_at ASC

GET  /api/pairs/{pair_id}
    path: pair_id: uuid.UUID
    response: ResponsePairOut
    # 404 if pair not found

POST /api/pairs/ingest-hhrlhf
    body: IngestHHRLHFRequest
    response: IngestResponse
    # Calls hhrlhf_ingestor.ingest_hhrlhf()
```

### `cai_api/routers/annotations.py`

```python
POST /api/annotations
    body: AnnotationBatch
    response: AnnotationBatchResponse
    # Validates principle_id in 1–10 for each rating (Pydantic handles this)
    # Inserts each PrincipleRating as a separate Annotation row
    # ON CONFLICT (pair_id, principle_id, annotator_id) DO UPDATE SET
    #   preferred = EXCLUDED.preferred,
    #   confidence = EXCLUDED.confidence,
    #   annotated_at = NOW()
    # Returns all created/updated Annotation rows
```

### `cai_api/routers/stats.py`

```python
GET /api/stats/principle-coverage
    response: PrincipleCoverageResponse
    # For each principle_id 1–10:
    #   annotation_count = COUNT(*) WHERE principle_id = N
    #   agreement_rate = COUNT(*) WHERE preferred != 'TIE' AND principle_id = N
    #                    / annotation_count (0.0 if annotation_count == 0)
    # Always returns 10 items (zero-filled for principles with no annotations)

GET /api/stats/rm-eval
    response: RMEvalResponse | {"detail": "No eval available"}
    # Calls eval_loader.load_latest_eval()
    # Returns 404 with detail message if no eval file exists

GET /api/stats/calibration
    response: CalibrationResponse | {"detail": "No eval available"}
    # Same eval file as rm-eval; extracts calibration bins section
    # Returns 404 if no eval file exists
```

### `scripts/generate_pairs.py`

```python
# CLI usage:
#   python scripts/generate_pairs.py --prompts-file prompts.txt --count 10
#
# For each line in prompts-file, generates 2 Ollama completions:
#   response_a: temperature=0.2 (careful)
#   response_b: temperature=0.9 (risky)
# Posts each pair to POST /api/pairs/ingest-ollama (or directly inserts — see note)
#
# Implementation note: directly inserts via httpx POST to API endpoint
# POST /api/pairs/ingest-ollama (not the hhrlhf endpoint)

def generate_pair(
    prompt: str,
    model: str,
    ollama_base_url: str,
) -> tuple[str, str]:
    """
    Call Ollama chat endpoint twice with same prompt.
    First call: temperature=0.2 → response_a
    Second call: temperature=0.9 → response_b
    Returns (response_a, response_b).
    Raises httpx.HTTPError if Ollama is unreachable.
    """
    ...

def run(prompts_file: Path, count: int, api_base_url: str, ollama_base_url: str) -> None:
    """
    CLI entry point. Reads prompts_file line by line.
    For each prompt (up to count), calls generate_pair() and POSTs to API.
    Prints inserted/skipped counts on completion.
    """
    ...
```

Note: Add `POST /api/pairs/ingest-ollama` endpoint alongside `ingest-hhrlhf`:
```python
POST /api/pairs/ingest-ollama
    body: OllamaIngestRequest  # { prompt, response_a, response_b }
    response: { pair_id: uuid }
    # Inserts single pair with source='generated'
    # No duplicate check needed (UUID always unique)
```

Add to `cai_api/schemas/pair.py`:
```python
class OllamaIngestRequest(BaseModel):
    prompt: str
    response_a: str
    response_b: str
```

### `cai_trainer/dataset_builder.py`

```python
from __future__ import annotations
from datasets import Dataset
from sqlalchemy import text
from sqlalchemy.engine import Engine


def build_rm_dataset(
    engine: Engine,
    train_split: float = 0.8,
    min_annotations: int = 50,
) -> tuple[Dataset, Dataset]:
    """
    Fetch all non-TIE annotations from the DB via SQLAlchemy sync engine.
    For each annotation:
        input_text = f"Principle {principle_id}: {PRINCIPLE_MAP[principle_id]} [SEP] {prompt} [SEP] {response_a} [SEP] {response_b}"
        label = 0 if preferred == 'A' else 1
    Raises ValueError(f"Only {n} non-TIE annotations found; minimum is {min_annotations}.") if count < min_annotations.
    Shuffle with seed=42. Split into train (train_split fraction) and eval (remainder).
    Returns (train_dataset, eval_dataset) as HuggingFace Dataset objects.
    Each row: {"text": str, "label": int}.
    """
    ...


def _build_annotation_query() -> text:
    """
    Returns SQLAlchemy text() query joining annotations + response_pairs.
    Filters: preferred IN ('A', 'B') — excludes TIE.
    Returns columns: principle_id, preferred, prompt, response_a, response_b.
    """
    ...
```

### `cai_trainer/train.py`

```python
# Entry point: uv run train-rm
# pyproject.toml: [project.scripts] train-rm = "cai_trainer.train:main"

from __future__ import annotations
from pathlib import Path
import typer


def main(
    output_dir: Path = typer.Option(..., help="Path to save checkpoint"),
    train_split: float = typer.Option(0.8, help="Fraction of data for training"),
    epochs: int = typer.Option(3, help="Training epochs"),
    batch_size: int = typer.Option(32, help="Per-device batch size (DistilBERT on MPS)"),
    warmup_steps: int = typer.Option(100, help="Warmup steps (not warmup_ratio — removed in transformers 5.2)"),
    learning_rate: float = typer.Option(2e-5, help="Learning rate"),
) -> None:
    """
    Train DistilBERT reward model on preference annotations.
    Device: MPS auto-detected by Trainer. Do NOT pass no_cuda or bf16.
    eval_strategy and save_strategy must both be 'epoch' (load_best_model_at_end=True).
    Saves checkpoint to output_dir via model.save_pretrained() + tokenizer.save_pretrained().
    Prints final train loss and eval accuracy on completion.
    """
    ...
```

**TrainingArguments configuration (implementer must use these exact field names):**

```python
from transformers import TrainingArguments

args = TrainingArguments(
    output_dir=str(output_dir),
    num_train_epochs=epochs,
    per_device_train_batch_size=batch_size,
    per_device_eval_batch_size=batch_size,
    warmup_steps=warmup_steps,          # NOT warmup_ratio (removed in transformers 5.2)
    learning_rate=learning_rate,
    weight_decay=0.01,
    eval_strategy="epoch",              # NOT evaluation_strategy
    save_strategy="epoch",              # must match eval_strategy when load_best_model_at_end=True
    load_best_model_at_end=True,
    metric_for_best_model="eval_accuracy",
    logging_steps=50,
    # bf16=False is the default; do NOT set it (MPS constraint)
    # no_cuda removed in transformers 5.x; do NOT set it
)
```

### `cai_trainer/evaluate.py`

```python
# Entry point: uv run evaluate-rm
# pyproject.toml: [project.scripts] evaluate-rm = "cai_trainer.evaluate:main"

from __future__ import annotations
from pathlib import Path
import typer


def main(
    checkpoint_dir: Path = typer.Option(..., help="Path to saved DistilBERT checkpoint"),
    output_file: Path = typer.Option(..., help="Path for eval JSON output"),
    train_split: float = typer.Option(0.8, help="Must match train-rm split to reproduce eval set"),
) -> None:
    """
    Rebuild eval dataset (same seed=42, same train_split) to get the held-out 20%.
    Run inference on eval set: collect logits, compute softmax probabilities.
    Per principle: filter eval rows, compute accuracy + AUC-ROC via sklearn.
    Compute calibration bins (10 equal-width) per principle via calibration.compute_calibration_bins().
    Write output_file as JSON matching RMEvalResponse schema.
    output_file path convention: resources/evals/cai-preference-trainer/<timestamp>.json
    where timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    """
    ...


def _run_inference(
    model,
    tokenizer,
    eval_dataset: Dataset,
    batch_size: int = 32,
) -> tuple[list[float], list[int]]:
    """
    Run batched inference on eval_dataset.
    Returns (predicted_probs, true_labels) where predicted_probs are softmax P(class=1).
    Uses torch.no_grad(). Moves model to MPS if available, else CPU.
    """
    ...
```

---

## API Contracts (Complete)

| Method | Path | Request Body | Response | Status Codes |
|--------|------|-------------|----------|--------------|
| POST | `/api/pairs/ingest-hhrlhf` | `IngestHHRLHFRequest` | `IngestResponse` | 200, 422 |
| POST | `/api/pairs/ingest-ollama` | `OllamaIngestRequest` | `{pair_id: str}` | 201, 422 |
| GET | `/api/pairs/queue` | — | `QueueResponse` | 200 |
| GET | `/api/pairs/{pair_id}` | — | `ResponsePairOut` | 200, 404 |
| POST | `/api/annotations` | `AnnotationBatch` | `AnnotationBatchResponse` | 201, 422, 409 (on principle_id range violation) |
| GET | `/api/stats/principle-coverage` | — | `PrincipleCoverageResponse` | 200 |
| GET | `/api/stats/rm-eval` | — | `RMEvalResponse` | 200, 404 |
| GET | `/api/stats/calibration` | — | `CalibrationResponse` | 200, 404 |

Query params for `/api/pairs/queue`: `annotator_id: str` (required), `limit: int = 20`, `offset: int = 0`.

---

## Frontend TypeScript Types

**`cai-preference-trainer-ui/src/types/api.ts`**

```typescript
export type PairSource = 'hhrlhf' | 'generated'
export type PreferredChoice = 'A' | 'B' | 'TIE'

export type QueueItem = {
  pair_id: string
  prompt: string  // truncated to 200 chars
  source: PairSource
  created_at: string  // ISO
  rated_principle_count: number  // 0–10
}

export type QueueResponse = {
  items: QueueItem[]
  total: number
  limit: number
  offset: number
}

export type ResponsePairOut = {
  pair_id: string
  prompt: string
  response_a: string
  response_b: string
  source: PairSource
  created_at: string
}

export type PrincipleRating = {
  principle_id: number  // 1–10
  preferred: PreferredChoice
  confidence: number | null  // 1–3 or null
}

export type AnnotationBatch = {
  pair_id: string
  annotator_id: string
  ratings: PrincipleRating[]
}

export type AnnotationOut = {
  annotation_id: string
  pair_id: string
  principle_id: number
  annotator_id: string
  preferred: PreferredChoice
  confidence: number | null
  annotated_at: string
}

export type AnnotationBatchResponse = {
  created: AnnotationOut[]
}

export type PrincipleCoverageItem = {
  principle_id: number
  principle_text: string
  annotation_count: number
  agreement_rate: number  // 0.0–1.0
}

export type PrincipleCoverageResponse = {
  principles: PrincipleCoverageItem[]
}

export type PrincipleEvalResult = {
  principle_id: number
  principle_text: string
  accuracy: number
  auc_roc: number
  n_eval_samples: number
}

export type RMEvalResponse = {
  checkpoint_dir: string
  trained_at: string
  total_train_samples: number
  total_eval_samples: number
  per_principle: PrincipleEvalResult[]
}

export type CalibrationBin = {
  bin_lower: number
  bin_upper: number
  predicted_prob_mean: number
  fraction_positive: number
  count: number
}

export type PrincipleCalibration = {
  principle_id: number
  bins: CalibrationBin[]
}

export type CalibrationResponse = {
  principles: PrincipleCalibration[]
}
```

---

## Frontend Hook Signatures

All hooks live in `src/hooks/`. All use TanStack Query v5.

```typescript
// useQueue.ts
export function useQueue(
  annotatorId: string,
  page: number = 0,
  limit: number = 20,
): UseQueryResult<QueueResponse, Error>
// refetchInterval: 30_000 (30 seconds)
// enabled: annotatorId.length > 0
// queryKey: ['queue', annotatorId, page, limit]

// usePair.ts
export function usePair(
  pairId: string | null,
): UseQueryResult<ResponsePairOut, Error>
// enabled: pairId !== null
// queryKey: ['pair', pairId]

// usePrincipleCoverage.ts
export function usePrincipleCoverage(): UseQueryResult<PrincipleCoverageResponse, Error>
// refetchInterval: 30_000
// queryKey: ['principle-coverage']

// useRMEval.ts
export function useRMEval(): UseQueryResult<RMEvalResponse | null, Error>
// Returns null data (not error) when API returns 404
// refetchInterval: false (user manually triggers by visiting tab)
// queryKey: ['rm-eval']

// useCalibration.ts
export function useCalibration(): UseQueryResult<CalibrationResponse | null, Error>
// Returns null data on 404
// refetchInterval: false
// queryKey: ['calibration']
```

---

## Frontend Component Props

```typescript
// AnnotationForm.tsx
type AnnotationFormProps = {
  pair: ResponsePairOut
  annotatorId: string
  onSubmitSuccess: () => void  // called after successful POST; triggers queue refetch
}
// Internal state: Record<number, { preferred: PreferredChoice; confidence: number | null }>
// Indexed by principle_id 1–10. Submit disabled until all 10 principles have a preferred value.
// Confidence is optional — null if annotator leaves blank.

// QueueList.tsx
type QueueListProps = {
  items: QueueItem[]
  selectedPairId: string | null
  onSelectPair: (pairId: string) => void
  isLoading: boolean
}
// Shows "Resume (N/10)" badge when rated_principle_count > 0 and < 10
// Shows "Start" for rated_principle_count === 0

// PrincipleCoverage.tsx
type PrincipleCoverageProps = {
  data: PrincipleCoverageResponse
}
// Renders a table: principle text | annotation count | agreement rate (%)
// agreement_rate displayed as percentage with one decimal place

// RMEvalCard.tsx
type RMEvalCardProps = {
  data: RMEvalResponse | null
}
// When null: renders "No eval results yet. Run evaluate-rm to populate."
// When present: table with principle, accuracy (%), AUC-ROC, n_eval_samples
// Model card section below table: checkpoint_dir, trained_at, total_train_samples

// CalibrationChart.tsx
type CalibrationChartProps = {
  principleCalibration: PrincipleCalibration
  height?: number  // default 250
}
// recharts LineChart: X axis = predicted prob (bin midpoints), Y axis = fraction positive
// Reference line at y=x (perfect calibration)
// Same visual pattern as llm-safety-monitor CalibrationChart
// Used in a loop in Calibration tab — one chart per principle
```

---

## Dependencies (Import Graph)

```
cai-preference-trainer-api/
    cai_api.main
        ← cai_api.routers.pairs
            ← cai_api.services.hhrlhf_ingestor
                ← cai_api.models.response_pair
                ← cai_api.schemas.pair
            ← cai_api.database
        ← cai_api.routers.annotations
            ← cai_api.models.annotation
            ← cai_api.schemas.annotation
        ← cai_api.routers.stats
            ← cai_api.services.calibration
            ← cai_api.services.eval_loader
                ← cai_api.schemas.stats
            ← cai_api.principles
        ← cai_api.config (pydantic-settings)
        ← cai_api.database (async engine)

cai-preference-trainer/
    cai_trainer.train
        ← cai_trainer.dataset_builder
            ← cai_trainer.principles
            ← sqlalchemy (sync)
        ← transformers.AutoModelForSequenceClassification
        ← transformers.AutoTokenizer
        ← transformers.Trainer
        ← transformers.TrainingArguments
        ← accelerate  (explicit dep — required by Trainer ≥5.x)
    cai_trainer.evaluate
        ← cai_trainer.dataset_builder
        ← cai_trainer.calibration
        ← sklearn.metrics (accuracy_score, roc_auc_score)

cai-preference-trainer-ui/
    App.tsx
        ← pages/Dashboard.tsx
            ← components/PrincipleCoverage.tsx ← hooks/usePrincipleCoverage.ts
            ← components/RMEvalCard.tsx        ← hooks/useRMEval.ts
            ← components/CalibrationChart.tsx  ← hooks/useCalibration.ts
            ← components/QueueList.tsx         ← hooks/useQueue.ts
        ← pages/Annotate.tsx
            ← components/QueueList.tsx         ← hooks/useQueue.ts
            ← components/AnnotationForm.tsx    ← hooks/usePair.ts
    types/api.ts  (imported by all hooks and components — no circular deps)
```

No circular dependencies. `principles.py` is a leaf node in both Python projects.

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Error handling (API) | FastAPI exception handlers for 404 (pair not found) and 422 (Pydantic validation). DB errors bubble to 500 — logged with `exc_info=True`. No silent fallbacks. |
| Error handling (trainer) | `ValueError` with descriptive message if annotation count < minimum. CLI exits with code 1 on unhandled exceptions. |
| Configuration (API) | `cai_api/config.py`: pydantic-settings `Settings` with `extra="ignore"`. Fields: `db_url: str`, `ollama_base_url: str = "http://localhost:11434"`, `evals_dir: Path`. Loaded from `.env`. |
| Configuration (trainer) | Same pattern: `cai_trainer/config.py` with `db_url: str` and `models_dir: Path`, `evals_dir: Path`. |
| Logging | `structlog` or stdlib `logging` at INFO level. Router-level logger per module. Training losses logged by HuggingFace Trainer to stdout — no custom logging needed in `train.py`. |
| DB migrations | Alembic. Migration `0001_initial_schema.py` creates both tables and ENUMs. `alembic upgrade head` idempotent. |
| CORS | FastAPI CORS middleware: `allow_origins=["http://localhost:5173"]` (Vite dev server). |
| Testing (API) | pytest + pytest-asyncio. `conftest.py` creates an async test engine against a test DB (separate `DB_URL_TEST` env var, or `cai_preference_trainer_test` DB). Fixtures: `async_session`, `seeded_pairs`, `seeded_annotations`. Aggregation endpoint tests (`test_stats.py`) assert computed values from seeded data, not just response shape. |
| Testing (trainer) | pytest with sync fixtures. `test_dataset_builder.py` inserts seeded annotations via direct DB and asserts TIEs are excluded and label encoding is correct. |
| MPS constraints | Do not pass `bf16`, `no_cuda`, or `pin_memory` to TrainingArguments. Use `warmup_steps` (integer), not `warmup_ratio` (removed in transformers 5.2). `eval_strategy` and `save_strategy` must both be `"epoch"` when `load_best_model_at_end=True`. Add `accelerate` as explicit dependency in `pyproject.toml`. |

---

## Implementation Notes

**RM input format:**
The input string for DistilBERT is:
```
f"Principle {principle_id}: {PRINCIPLE_MAP[principle_id]} [SEP] {prompt} [SEP] {response_a} [SEP] {response_b}"
```
`[SEP]` here is a literal string used as a natural-language separator — not the `[SEP]` token. The tokenizer inserts its own `[SEP]` tokens at sequence boundaries. DistilBERT's max sequence length is 512 tokens. Long prompts + responses may be truncated — `tokenizer(..., truncation=True, max_length=512)`. This is acceptable for v1.

**Training dataset size:**
For N non-TIE annotations, the RM dataset has exactly N rows (one per annotation, not one per pair). Each row represents one annotator's preference for one principle for one pair. The `10x` multiplier (10 principles × N pairs) applies only when every pair has been annotated across all 10 principles — in practice the dataset size equals the non-TIE annotation count.

**Minimum annotation threshold:**
50 non-TIE annotations is the `min_annotations` default in `build_rm_dataset()`. This is a guard against training on too little data. The CLI raises `ValueError` clearly. This value is not configurable in v1 — hardcoded as a constant in `dataset_builder.py`: `MIN_ANNOTATIONS = 50`.

**TIE handling:**
TIE annotations are stored in the DB (they count toward `annotation_count` in principle-coverage stats and toward `rated_principle_count` in the queue). They are excluded from RM training by the `preferred IN ('A', 'B')` filter in `_build_annotation_query()`. They are also excluded from `agreement_rate` computation (agreement_rate = % non-TIE = preferred IN ('A', 'B') / total).

**HH-RLHF prompt extraction — exact implementation:**
```python
def _parse_hhrlhf_row(row: dict) -> tuple[str, str, str]:
    chosen = row["chosen"]
    rejected = row["rejected"]
    # Both start with "\n\nHuman: <prompt>\n\nAssistant: <response>"
    # Split on last "\n\nAssistant: " to get prompt and response_a
    parts = chosen.rsplit("\n\nAssistant: ", maxsplit=1)
    if len(parts) != 2:
        raise ValueError(f"Unexpected chosen format: {chosen[:100]!r}")
    prompt = parts[0].removeprefix("\n\nHuman: ").strip()
    response_a = parts[1].strip()
    # rejected has same prompt; extract only response_b
    rej_parts = rejected.rsplit("\n\nAssistant: ", maxsplit=1)
    if len(rej_parts) != 2:
        raise ValueError(f"Unexpected rejected format: {rejected[:100]!r}")
    response_b = rej_parts[1].strip()
    return prompt, response_a, response_b
```

**Ollama pair generation — exact API call:**
```python
# POST http://localhost:11434/api/chat
{
    "model": "qwen2.5-coder:7b",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.2,  # or 0.9
    "stream": False
}
# Response: {"message": {"content": "<response text>"}}
```

**Eval JSON format** (written by `evaluate-rm`, read by `eval_loader.py`):
```json
{
  "checkpoint_dir": "/abs/path/to/checkpoint",
  "trained_at": "2026-06-06T12:00:00+00:00",
  "total_train_samples": 120,
  "total_eval_samples": 30,
  "per_principle": [
    {
      "principle_id": 1,
      "principle_text": "...",
      "accuracy": 0.73,
      "auc_roc": 0.81,
      "n_eval_samples": 3,
      "calibration_bins": [
        {"bin_lower": 0.0, "bin_upper": 0.1, "predicted_prob_mean": 0.05, "fraction_positive": 0.0, "count": 1},
        ...
      ]
    }
  ]
}
```
The API's `CalibrationResponse` is assembled from the `calibration_bins` field of each principle in the eval JSON.

**Queue SQL pattern:**
```sql
SELECT
    rp.pair_id,
    LEFT(rp.prompt, 200) AS prompt,
    rp.source,
    rp.created_at,
    COALESCE(a.rated_count, 0) AS rated_principle_count
FROM response_pairs rp
LEFT JOIN (
    SELECT pair_id, COUNT(*) AS rated_count
    FROM annotations
    WHERE annotator_id = :annotator_id
    GROUP BY pair_id
) a ON a.pair_id = rp.pair_id
WHERE COALESCE(a.rated_count, 0) < 10
ORDER BY rp.created_at ASC
LIMIT :limit OFFSET :offset;
```

**Annotator ID localStorage pattern (frontend):**
```typescript
// src/hooks/useAnnotatorId.ts
export function useAnnotatorId(): [string, (id: string) => void] {
  const [annotatorId, setAnnotatorId] = useState<string>(
    () => localStorage.getItem('cai_annotator_id') ?? ''
  )
  const setAndPersist = (id: string) => {
    localStorage.setItem('cai_annotator_id', id)
    setAnnotatorId(id)
  }
  return [annotatorId, setAndPersist]
}
```
Used in `Annotate.tsx`: if `annotatorId === ''`, render a modal with a single text input before showing the queue.

**pyproject.toml scripts (cai-preference-trainer/):**
```toml
[project.scripts]
train-rm = "cai_trainer.train:main"
evaluate-rm = "cai_trainer.evaluate:main"
```

---

## Handoff

**Next role:** implementer

The implementer reads this file and begins coding immediately. All design decisions are resolved. No open questions remain.

**Implementation order (recommended):**

1. `cai-preference-trainer-api/`: DB schema + Alembic migration → models → config + database → schemas → services → routers → main.py
2. `scripts/generate_pairs.py` — standalone, tests Ollama connectivity
3. `cai-preference-trainer/`: dataset_builder → train.py → evaluate.py
4. `cai-preference-trainer-ui/`: types/api.ts → hooks → components → pages → App.tsx routing

**Flags for implementer:**

- `accelerate` must be an explicit dependency in `cai-preference-trainer/pyproject.toml`. It is a hard runtime dep of `transformers.Trainer` ≥5.x and is not auto-installed.
- Do not pass `warmup_ratio` to `TrainingArguments` — it was removed in transformers 5.2. Use `warmup_steps` (int).
- `eval_strategy` and `save_strategy` must both be `"epoch"` when `load_best_model_at_end=True`. Mismatched values raise at `Trainer.__init__`.
- The `useAnnotatorId` hook is a required addition not listed in the component props — add it to `src/hooks/useAnnotatorId.ts` as a separate file.
- `test_stats.py` must include at least one test with seeded annotations that asserts `agreement_rate` is computed correctly (not just that the endpoint returns 200).
- `principles.json` in the frontend (`src/principles.json`) must be manually kept in sync with `principles.py`. In v1 this is a one-time copy — principles do not change.
