# Architect Output — red-team-platform

**Role:** architect
**Sequence:** `new-project-full` (step 3)
**Date:** 2026-06-07
**Base:** extends `roles/architect/archive/2026-06-06-red-team-platform-output.md`

This file records changes and additions only. Where a section matches the 2026-06-06 output exactly, it is noted as unchanged. The implementer reads both files — this file takes precedence on any conflict.

---

## System Overview

Same as 2026-06-06 output, with three changes:
1. Corpus source is `sevdeawesome/jailbreak_success` (replaces JailbreakBench + AdvBench).
2. `harm_category` is assigned by the taxonomy classifier at seed time (not sourced from the dataset directly).
3. A new failure clustering subsystem: `uv run cluster` CLI → `failure_clusters` + `cluster_summaries` tables → `GET /clusters` + `GET /clusters/{cluster_id}/members` endpoints → `FailureClusters` tab.

Updated data flow:
```
seed-corpus CLI → taxonomy_classifier → attacks table
                                      ↓
attack CLI → Ollama → pair_classifier → runs table + run_sessions table
                                      ↓
cluster CLI → TF-IDF + KMeans → failure_clusters + cluster_summaries tables
                                      ↓
FastAPI endpoints → React dashboard (6 tabs)
```

---

## Open Questions Resolved

**OQ1 — Sevdeawesome field names.**
Dataset: `sevdeawesome/jailbreak_success`. Based on the HuggingFace dataset card, likely fields are `jailbreak_query` (the full jailbreak prompt including any framing), `strategy` (the jailbreak technique name, e.g. "AIM", "DAN", "UCAR"), and `behavior` (the underlying harmful goal in plain text — this is what we feed to the taxonomy classifier).

Constants in `src/corpus/constants.py`:
```python
SEV_DATASET_NAME = "sevdeawesome/jailbreak_success"
SEV_SPLIT = "train"
SEV_ATTACK_TEXT_FIELD = "jailbreak_query"
SEV_STRATEGY_FIELD = "strategy"
SEV_HARM_GOAL_FIELD = "behavior"
SEV_SOURCE_KEY = "sevdeawesome"
```
**Implementer must verify these before writing the loader.** Run:
```python
from datasets import load_dataset
ds = load_dataset("sevdeawesome/jailbreak_success", split="train[:5]")
print(ds.features)
print(ds[0])
```
If field names differ, update `constants.py` only. No other file references field names directly.

**OQ2 — Taxonomy classifier output format.**
Load with `pipeline("text-classification", model=str(model_path), device=-1, top_k=1)`. Returns `[[{"label": "...", "score": float}]]`. Extract `result[0][0]["label"]`. The label string is the raw WildGuard category name as trained (e.g. `"toxic_language_hate_speech"`, `"violence_and_physical_harm"`). These are the same strings stored in `attacks.harm_category`.

Verify label format by inspecting the taxonomy checkpoint's `config.json` — the `id2label` mapping lists exact label strings. The implementer checks this before writing `classify_category()`.

**OQ3 — Cluster overwrite strategy.**
Full DELETE + INSERT in v1. No versioning column. Rationale: clustering is deterministic given the same input data and `CLUSTER_K`. The `cluster_summaries.computed_at` timestamp tells the user when the last cluster run occurred.

**OQ4 — coverage_summary refresh.**
Plain `REFRESH MATERIALIZED VIEW coverage_summary` (not CONCURRENTLY) — consistent with 2026-06-06 decision.

**OQ5 — Backend port.**
Port 8003. Locked in `.env.example` and `pyproject.toml` scripts block.

---

## Data Models

### New/Changed ORM Models (`src/models.py`)

The `Attack`, `RunSession`, and `Run` models are unchanged from the 2026-06-06 output.

**New models:**

```python
class FailureCluster(Base):
    __tablename__ = "failure_clusters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id: Mapped[int] = mapped_column(Integer, nullable=False)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("runs.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("ix_failure_clusters_cluster_id", "cluster_id"),
        Index("ix_failure_clusters_run_id", "run_id"),
    )

class ClusterSummary(Base):
    __tablename__ = "cluster_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    top_harm_category: Mapped[str] = mapped_column(String(100), nullable=False)
    top_strategy: Mapped[str] = mapped_column(String(100), nullable=False)
    representative_text: Mapped[str] = mapped_column(Text, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("uix_cluster_summaries_cluster_id", "cluster_id", unique=True),
    )
```

### Updated Settings (`src/config.py`)

```python
class Settings(BaseSettings):
    database_url: str
    sync_database_url: str                          # NEW — psycopg2 URL for cluster CLI
    pair_classifier_path: Path
    taxonomy_classifier_path: Path                  # NEW
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"
    ollama_timeout_s: int = 120
    cluster_k: int = 8                              # NEW

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

### New Pydantic Schemas (`src/api/schemas.py`)

Existing schemas are unchanged from the 2026-06-06 output.

**New schemas:**

```python
class ClusterSummaryOut(BaseModel):
    cluster_id: int
    size: int
    top_harm_category: str
    top_strategy: str
    representative_text: str
    computed_at: datetime

    model_config = {"from_attributes": True}

class ClustersOut(BaseModel):
    summaries: list[ClusterSummaryOut]

class ClusterMemberOut(BaseModel):
    run_id: uuid.UUID
    cluster_id: int
    attack_text: str
    harm_category: str
    strategy: str
    classifier_score: float
    jailbreak_success: bool
    latency_ms: int
    model_name: str

class ClusterMembersOut(BaseModel):
    cluster_id: int
    members: list[ClusterMemberOut]
```

### Updated `AttackRecord` dataclass (`src/corpus/loader.py`)

```python
@dataclass
class AttackRecord:
    source: str
    source_id: str
    harm_category: str   # set by seeder after taxonomy classification; empty string from loader
    strategy: str
    attack_text: str
    harm_goal: str       # NEW — fed to taxonomy_classifier; not persisted to DB
```

---

## Module Interfaces

### `src/runner/taxonomy_classifier.py` — NEW

```python
from __future__ import annotations
from pathlib import Path

_pipeline = None  # module-level singleton

def get_taxonomy_classifier(model_path: Path | None = None):
    """
    Returns the loaded transformers pipeline (text-classification, top_k=1).
    On first call: loads from model_path (or settings.taxonomy_classifier_path if None).
    Subsequent calls: returns cached pipeline regardless of model_path argument.
    Raises RuntimeError if model_path does not contain config.json.
    """
    global _pipeline
    ...

def classify_category(text: str) -> str:
    """
    Runs the taxonomy classifier on text.
    Returns the top-scoring category label string (e.g. "toxic_language_hate_speech").
    Calls get_taxonomy_classifier() — raises RuntimeError if not initialised.
    """
    ...
```

### `src/cluster/kmeans.py` — NEW

```python
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class ClusterResult:
    cluster_id: int
    run_id: str            # UUID as string
    attack_text: str
    harm_category: str
    strategy: str
    classifier_score: float

@dataclass
class ClusterSummaryResult:
    cluster_id: int
    size: int
    top_harm_category: str
    top_strategy: str
    representative_text: str  # attack_text of run closest to centroid

def cluster_failures(
    rows: list[dict],       # {run_id, attack_text, harm_category, strategy, classifier_score}
    k: int,
) -> tuple[list[ClusterResult], list[ClusterSummaryResult]]:
    """
    Vectorises attack_text with TfidfVectorizer(max_features=5000, stop_words='english').
    Clusters with KMeans(n_clusters=k, random_state=42, n_init='auto').
    For each cluster: representative = row with minimum euclidean distance to centroid;
    top_harm_category and top_strategy = mode across cluster members.
    Returns (cluster_results, summary_results).
    Raises ValueError if len(rows) < k.
    Pure function — no DB calls.
    """
    ...

def main() -> None:
    """
    CLI entry point: uv run cluster.
    1. Queries jailbreak_success=True runs via sync DB session.
    2. Raises with clear message if count < settings.cluster_k.
    3. Calls cluster_failures(rows, settings.cluster_k).
    4. Opens sync DB session; DELETE FROM failure_clusters + cluster_summaries.
    5. Bulk-inserts results.
    6. Prints summary table.
    """
    ...
```

### `src/corpus/loader.py` — UPDATED

```python
def load_sevdeawesome() -> list[AttackRecord]:
    """
    Loads sevdeawesome/jailbreak_success from HuggingFace (cached after first pull).
    Uses constants from src/corpus/constants.py.
    Sets harm_goal from SEV_HARM_GOAL_FIELD; leaves harm_category as empty string.
    source_id = f"sev-{row_index}".
    Logs a warning and skips malformed rows (missing required fields).
    """
    ...
```

### `src/corpus/seed.py` — UPDATED

```python
async def seed_corpus(
    session: AsyncSession,
    records: list[AttackRecord],
) -> tuple[int, int]:
    """
    For each record:
      1. Calls taxonomy_classifier.classify_category(record.harm_goal).
      2. Sets record.harm_category to the returned label.
      3. Upserts into attacks table on (source, source_id) conflict.
         On conflict: updates harm_category, strategy, attack_text.
    Returns (inserted_count, updated_count).
    Taxonomy classifier must be loaded before calling (get_taxonomy_classifier() in main()).
    """
    ...

def main() -> None:
    """
    CLI entry point: uv run seed-corpus.
    1. Calls get_taxonomy_classifier() — fails fast if path invalid.
    2. Loads records via load_sevdeawesome().
    3. Calls seed_corpus(session, records).
    4. Prints summary: Seeded N, updated M.
    """
    ...
```

### `src/api/routers/clusters.py` — NEW

```python
# GET /clusters
# Returns: ClustersOut
# SQL: SELECT * FROM cluster_summaries ORDER BY size DESC

# GET /clusters/{cluster_id}/members
# Path param: cluster_id (int)
# Returns: ClusterMembersOut
# SQL: SELECT fc.cluster_id, fc.run_id, a.attack_text, a.harm_category, a.strategy,
#             r.classifier_score, r.jailbreak_success, r.latency_ms, r.model_name
#      FROM failure_clusters fc
#      JOIN runs r ON fc.run_id = r.id
#      JOIN attacks a ON r.attack_id = a.id
#      WHERE fc.cluster_id = :cluster_id
#      ORDER BY r.classifier_score DESC
# Raises 404 if cluster_id not in cluster_summaries.
```

All other routers are unchanged from the 2026-06-06 output.

---

## DB Schema Additions (Migration `001_initial_schema.py`)

Add to the 2026-06-06 migration:

```sql
-- failure_clusters
CREATE TABLE failure_clusters (
    id          UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id  INTEGER NOT NULL,
    run_id      UUID    NOT NULL REFERENCES runs(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_failure_clusters_cluster_id ON failure_clusters (cluster_id);
CREATE INDEX ix_failure_clusters_run_id     ON failure_clusters (run_id);

-- cluster_summaries
CREATE TABLE cluster_summaries (
    id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id        INTEGER      NOT NULL,
    size              INTEGER      NOT NULL,
    top_harm_category VARCHAR(100) NOT NULL,
    top_strategy      VARCHAR(100) NOT NULL,
    representative_text TEXT       NOT NULL,
    computed_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX uix_cluster_summaries_cluster_id ON cluster_summaries (cluster_id);
```

---

## Frontend Types (`web/src/types/index.ts`)

All existing types from the 2026-06-06 output are unchanged. Add:

```typescript
export type ClusterSummary = {
  cluster_id: number
  size: number
  top_harm_category: string
  top_strategy: string
  representative_text: string
  computed_at: string
}

export type ClustersOut = {
  summaries: ClusterSummary[]
}

export type ClusterMember = {
  run_id: string
  cluster_id: number
  attack_text: string
  harm_category: string
  strategy: string
  classifier_score: number
  jailbreak_success: boolean
  latency_ms: number
  model_name: string
}

export type ClusterMembersOut = {
  cluster_id: number
  members: ClusterMember[]
}
```

---

## Frontend Hooks

All hooks from the 2026-06-06 output are unchanged. Add:

```typescript
// useClusters.ts
function useClusters(): UseQueryResult<ClustersOut>
// refetchInterval: none

// useClusterMembers.ts
function useClusterMembers(clusterId: number | null): UseQueryResult<ClusterMembersOut>
// enabled: clusterId !== null
// refetchInterval: none
```

---

## `FailureClusters.tsx` Component Spec

Props: none.
- State: `expandedClusterId: number | null`.
- Uses: `useClusters()`, `useClusterMembers(expandedClusterId)`.
- Empty state (summaries.length === 0): message — "No failure clusters yet. Run `uv run cluster` after an attack session."
- Grid of cluster cards (2 columns, gap-4):
  - Header: `Cluster {cluster_id}` badge + `{size} failures` text.
  - Chips: `top_harm_category` (red/rose tint), `top_strategy` (amber tint).
  - Representative text: truncated to 120 chars, `font-mono text-sm bg-muted px-2 py-1 rounded`.
  - "Show members" / "Hide members" toggle button. Click: `setExpandedClusterId(id)` / `null`.
- Expanded members panel (renders below grid when expandedClusterId !== null):
  - Loading spinner while `useClusterMembers` fetches.
  - Table: attack_text (80 char truncation), harm_category, strategy, classifier_score (toFixed(2)), latency_ms.
  - "Close" button.

---

## Updated `.env.example` (backend)

```
DATABASE_URL=postgresql+asyncpg://redteam:redteam@localhost:5435/redteam
SYNC_DATABASE_URL=postgresql+psycopg2://redteam:redteam@localhost:5435/redteam
PAIR_CLASSIFIER_PATH=/absolute/path/to/resources/models/llm-safety-monitor/pair-2026-06-07
TAXONOMY_CLASSIFIER_PATH=/absolute/path/to/resources/models/llm-safety-monitor/taxonomy-2026-06-07
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
OLLAMA_TIMEOUT_S=120
CLUSTER_K=8
ALLOWED_ORIGINS=http://localhost:5173
API_PORT=8003
```

## Updated `pyproject.toml` scripts block

```toml
[tool.uv.scripts]
seed-corpus = "red_team_platform.corpus.seed:main"
attack      = "red_team_platform.runner.attack:main"
cluster     = "red_team_platform.cluster.kmeans:main"
api         = "uvicorn red_team_platform.api.main:create_app --factory --reload --port 8003"
```

---

## Updated Import Graph (additions only)

```
src/runner/taxonomy_classifier.py   ← NEW
    imports: src/config.py, transformers (deferred)
    ← imported by: src/corpus/seed.py

src/cluster/kmeans.py               ← NEW
    imports: src/config.py, src/models.py, sklearn (deferred), sqlalchemy sync

src/api/routers/clusters.py         ← NEW
    imports: src/api/deps.py, src/api/schemas.py, src/models.py
    ← registered by: src/api/main.py
```

No circular dependencies introduced.

---

## Implementation Notes

### Sevdeawesome Dataset Loading

If `load_dataset(SEV_DATASET_NAME)` raises `ValueError: Config name is missing`, use:
```python
from datasets import get_dataset_config_names
configs = get_dataset_config_names("sevdeawesome/jailbreak_success")
ds = load_dataset("sevdeawesome/jailbreak_success", configs[0], split="train")
```

### Taxonomy Label Format

Inspect the checkpoint's `id2label` before writing `classify_category()`:
```python
import json
from pathlib import Path
config = json.loads((Path(settings.taxonomy_classifier_path) / "config.json").read_text())
print(config["id2label"])
```
Label strings are the ground truth. Do not assume they match human-readable category names exactly.

### KMeans Representative Selection

```python
import numpy as np
from sklearn.metrics.pairwise import euclidean_distances

for cluster_id in range(k):
    mask = labels == cluster_id
    cluster_vectors = X[mask]  # sparse matrix slice
    centroid = kmeans.cluster_centers_[cluster_id]
    distances = euclidean_distances(cluster_vectors, centroid.reshape(1, -1)).flatten()
    representative_idx = np.argmin(distances)
    representative_text = cluster_rows[mask][representative_idx]["attack_text"]
```

### Sync DB Session in Cluster CLI

```python
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

engine = create_engine(settings.sync_database_url, pool_pre_ping=True)
with Session(engine) as session:
    session.execute(delete(FailureCluster))
    session.execute(delete(ClusterSummary))
    session.bulk_save_objects([FailureCluster(...) for r in cluster_results])
    session.bulk_save_objects([ClusterSummary(...) for s in summary_results])
    session.commit()
```

---

## Handoff

**Next role:** implementer

The implementer reads this file AND `roles/architect/archive/2026-06-06-red-team-platform-output.md`. This file takes precedence on all conflicts. The 2026-06-06 file provides the full detail for unchanged sections (complete ORM for Attack/Run/RunSession, all existing router specs, heatmap rendering, regression line grouping, docker-compose.yml, test patterns).

**Implementation order:**
1. `pyproject.toml` + `.env` + `docker-compose.yml` — scaffold
2. `src/models.py` (all 5 ORM classes) + `src/config.py` + `src/db.py`
3. Alembic migration `001_initial_schema.py` — run `alembic upgrade head`
4. Inspect sevdeawesome fields → write `src/corpus/constants.py`
5. `src/corpus/loader.py` + `src/runner/taxonomy_classifier.py` + `src/corpus/seed.py`
6. `src/runner/classifier.py` + `src/runner/ollama_client.py` + `src/runner/attack.py`
7. `src/cluster/kmeans.py`
8. `src/api/schemas.py` + `src/api/deps.py` + all 7 routers + `src/api/main.py`
9. `web/` scaffold → `types/index.ts` → hooks (9 total) → 6 page components
10. pytest suite → vitest suite → `benchmarks/results.md` stub

**Critical flags:**
- Inspect sevdeawesome field names (step 4) before writing any loader code.
- Inspect taxonomy `config.json` `id2label` before writing `classify_category()`.
- Pair classifier checkpoint: `pair-2026-06-07` (not `pair-classifier` — that alias is stale).
- `coverage_summary` refresh: plain `REFRESH`, not `CONCURRENTLY`.
- Cluster CLI uses sync SQLAlchemy (psycopg2), not asyncpg.
- `transformers.pipeline` import deferred inside both `get_classifier()` and `get_taxonomy_classifier()`.
