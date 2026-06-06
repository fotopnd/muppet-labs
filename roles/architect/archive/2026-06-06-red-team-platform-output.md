# Architect Output — red-team-platform

**Role:** architect
**Sequence:** `new-project-full` (step 3)
**Date:** 2026-06-06

---

## System Overview

The red-team-platform is a local offensive safety evaluation system with four moving parts: a corpus seeder that ingests JailbreakBench and AdvBench from HuggingFace into Postgres; an attack runner CLI that fires each attack prompt at a local Ollama LLM and scores responses with a shared DistilBERT pair-classifier checkpoint; a FastAPI backend that serves aggregated evaluation data; and a 5-tab React dashboard that visualises coverage, strategy comparison, regression, and sample inspection. All components share a single PostgreSQL database on port 5435. The pair-classifier checkpoint lives in the workspace-shared `resources/models/` directory and is read-only from this project's perspective. No external API calls occur at runtime — Ollama and the classifier both run locally.

Data flow: `seed-corpus` CLI → `attacks` table → `attack` CLI → Ollama → `pair_classifier` → `runs` table + `run_sessions` table → materialised view `coverage_summary` → FastAPI endpoints → React dashboard.

---

## Open Questions Resolved

**OQ1 — coverage_summary session scoping:**
Aggregate across ALL runs, not scoped to a single session. The heatmap is most meaningful when it shows the full picture of what was tested and what succeeded. Session-level filtering is deferred to v2. The `coverage_summary` view does not filter by `session_id`.

**OQ2 — Ollama request timeout:**
120 seconds per request, configured via `OLLAMA_TIMEOUT_S` env var (default: 120). `httpx.AsyncClient` is instantiated with `timeout=httpx.Timeout(settings.ollama_timeout_s)`. This is set in `ollama_client.py`, not in the runner loop.

**OQ3 — pair_classifier loading strategy:**
Load once per process using a module-level singleton initialised on first call. FastAPI calls `get_classifier()` in a `@app.on_event("startup")` handler to force early initialisation and fail fast if the path is invalid. The attack runner CLI calls `get_classifier()` at startup before the loop begins. Both share the same `classifier.py` module — same singleton, same fail-fast behaviour.

**OQ4 — coverage_summary UNIQUE index:**
`CREATE UNIQUE INDEX uix_coverage_summary_category_strategy ON coverage_summary (harm_category, strategy)`. This is required for `REFRESH MATERIALIZED VIEW CONCURRENTLY`. Included in migration `001_initial_schema.py`.

---

## Data Models

### SQLAlchemy ORM (`src/models.py`)

```python
from __future__ import annotations
import uuid
from datetime import datetime, UTC
from sqlalchemy import String, Text, Boolean, Float, Integer, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Attack(Base):
    __tablename__ = "attacks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50), nullable=False)       # "jailbreakbench" | "advbench"
    source_id: Mapped[str] = mapped_column(String(200), nullable=False)   # original dataset row key
    harm_category: Mapped[str] = mapped_column(String(100), nullable=False)
    strategy: Mapped[str] = mapped_column(String(100), nullable=False)    # "GCG" | "AutoDAN" | "direct" | "unknown"
    attack_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    runs: Mapped[list[Run]] = relationship("Run", back_populates="attack")

    __table_args__ = (
        Index("uix_attacks_source_source_id", "source", "source_id", unique=True),
        Index("ix_attacks_harm_category", "harm_category"),
        Index("ix_attacks_strategy", "strategy"),
    )

class RunSession(Base):
    __tablename__ = "run_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)  # value of OLLAMA_MODEL
    total_attacks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_successes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    asr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # written at session close
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    runs: Mapped[list[Run]] = relationship("Run", back_populates="session")

    __table_args__ = (
        Index("ix_run_sessions_model_name", "model_name"),
        Index("ix_run_sessions_created_at", "created_at"),
    )

class Run(Base):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("run_sessions.id"), nullable=False)
    attack_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("attacks.id"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    jailbreak_success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    classifier_score: Mapped[float] = mapped_column(Float, nullable=False)  # unsafe class probability [0,1]
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    session: Mapped[RunSession] = relationship("RunSession", back_populates="runs")
    attack: Mapped[Attack] = relationship("Attack", back_populates="runs")

    __table_args__ = (
        Index("ix_runs_session_id", "session_id"),
        Index("ix_runs_attack_id", "attack_id"),
        Index("ix_runs_jailbreak_success", "jailbreak_success"),
    )
```

### Pydantic Settings (`src/config.py`)

```python
from __future__ import annotations
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str                            # postgresql+asyncpg://...  port 5435
    pair_classifier_path: Path                   # absolute path to checkpoint dir
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"
    ollama_timeout_s: int = 120

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

def get_settings() -> Settings:
    return Settings()
```

### Pydantic API Schemas (`src/api/schemas.py`)

```python
from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel

# --- Attacks ---
class AttackOut(BaseModel):
    id: uuid.UUID
    source: str
    source_id: str
    harm_category: str
    strategy: str
    attack_text: str
    created_at: datetime

    model_config = {"from_attributes": True}

class AttackListOut(BaseModel):
    items: list[AttackOut]
    total: int
    page: int
    page_size: int

# --- Sessions ---
class SessionOut(BaseModel):
    id: uuid.UUID
    model_name: str
    total_attacks: int
    total_successes: int
    asr: float
    created_at: datetime

    model_config = {"from_attributes": True}

# --- Runs ---
class RunOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    attack_id: uuid.UUID
    model_name: str
    response_text: str
    jailbreak_success: bool
    classifier_score: float
    latency_ms: int
    created_at: datetime
    # joined fields
    harm_category: str
    strategy: str
    attack_text: str

    model_config = {"from_attributes": True}

class RunListOut(BaseModel):
    items: list[RunOut]
    total: int
    page: int
    page_size: int

# --- Sample Review ---
class SampleOut(BaseModel):
    run_id: uuid.UUID
    attack_text: str
    response_text: str
    harm_category: str
    strategy: str
    jailbreak_success: bool
    classifier_score: float
    latency_ms: int
    model_name: str
    session_id: uuid.UUID
    created_at: datetime

# --- Coverage Heatmap ---
class CoverageCell(BaseModel):
    harm_category: str
    strategy: str
    total_runs: int
    total_successes: int
    asr: float          # attack success rate [0,1]

class CoverageOut(BaseModel):
    cells: list[CoverageCell]
    harm_categories: list[str]   # sorted unique values (for axis labels)
    strategies: list[str]        # sorted unique values (for axis labels)

# --- Strategy Comparison ---
class StrategyBar(BaseModel):
    strategy: str
    total_runs: int
    total_successes: int
    asr: float

class StrategyComparisonOut(BaseModel):
    bars: list[StrategyBar]

# --- Regression Tracker ---
class RegressionPoint(BaseModel):
    session_id: uuid.UUID
    model_name: str
    asr: float
    total_attacks: int
    created_at: datetime

class RegressionOut(BaseModel):
    points: list[RegressionPoint]  # ordered by created_at asc
    model_names: list[str]          # unique model names present (for legend)

# --- Filter helpers ---
class FilterValuesOut(BaseModel):
    values: list[str]
```

### Internal Data Transfer Objects (`src/corpus/loader.py`)

```python
from dataclasses import dataclass

@dataclass
class AttackRecord:
    source: str          # "jailbreakbench" | "advbench"
    source_id: str       # unique key within source dataset
    harm_category: str
    strategy: str
    attack_text: str
```

---

## Module Interfaces

### `src/config.py`

```python
def get_settings() -> Settings: ...
# Returns a cached Settings instance. Call once; module-level `settings = get_settings()` is fine.
```

### `src/db.py`

```python
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

def create_engine(database_url: str) -> AsyncEngine: ...
    # Returns asyncpg engine. Called once at app startup.

def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]: ...
    # Returns a session factory. Stored on app.state.

async def get_db_session() -> AsyncGenerator[AsyncSession, None]: ...
    # FastAPI dependency. Yields a session, commits on success, rolls back on exception.
```

### `src/corpus/constants.py`

```python
# JailbreakBench HuggingFace field names
JBB_DATASET_NAME = "JailbreakBench/JailbreakBench"
JBB_GOAL_FIELD = "Goal"
JBB_CATEGORY_FIELD = "Category"
JBB_JAILBREAKS_FIELD = "jailbreaks"
JBB_JAILBREAK_PROMPT_FIELD = "prompt"        # within each jailbreaks[] item
JBB_JAILBREAK_METHOD_FIELD = "method"        # within each jailbreaks[] item — maps to strategy
JBB_DEFAULT_STRATEGY = "direct"             # used when jailbreaks list is empty (direct attacks)
JBB_UNKNOWN_STRATEGY = "unknown"            # used when method field is missing

# AdvBench HuggingFace field names
ABB_DATASET_NAME = "llm-attacks/advbench"
ABB_SPLIT = "train"
ABB_GOAL_FIELD = "goal"
ABB_DEFAULT_CATEGORY = "general_harm"
ABB_DEFAULT_STRATEGY = "direct"
```

### `src/corpus/loader.py`

```python
from __future__ import annotations
import logging
from src.corpus.constants import *

logger = logging.getLogger(__name__)

def load_jailbreakbench() -> list[AttackRecord]:
    """
    Loads JailbreakBench/JailbreakBench from HuggingFace datasets.
    Uses cache after first pull. Each jailbreaks[] item becomes one AttackRecord.
    When jailbreaks list is empty, the Goal itself becomes the attack text with strategy="direct".
    When method field is missing from a jailbreak item, strategy="unknown" and a warning is emitted.
    source_id = f"jbb-{row_index}-{jailbreak_index}" (stable across re-loads for same dataset version).
    """
    ...

def load_advbench() -> list[AttackRecord]:
    """
    Loads llm-attacks/advbench from HuggingFace datasets.
    Each row becomes one AttackRecord with harm_category="general_harm" and strategy="direct".
    source_id = f"abb-{row_index}" (stable across re-loads).
    """
    ...
```

### `src/corpus/seed.py`

```python
from __future__ import annotations

async def seed_corpus(
    session: AsyncSession,
    records: list[AttackRecord],
) -> tuple[int, int]:
    """
    Upserts AttackRecord list into the attacks table.
    Upsert key: (source, source_id).
    Returns (inserted_count, skipped_count).
    """
    ...

def main() -> None:
    """
    CLI entry point: uv run seed-corpus.
    Loads JailbreakBench + AdvBench, calls seed_corpus, prints summary.
    """
    ...
```

### `src/runner/ollama_client.py`

```python
from __future__ import annotations
import httpx

async def chat(
    client: httpx.AsyncClient,
    model: str,
    prompt: str,
) -> tuple[str, int]:
    """
    POSTs to {OLLAMA_BASE_URL}/api/chat with stream=false.
    Returns (response_text, latency_ms).
    Raises httpx.HTTPStatusError on non-2xx.
    Raises httpx.TimeoutException on timeout (propagated to runner for logging).
    """
    ...

def make_client(base_url: str, timeout_s: int) -> httpx.AsyncClient:
    """
    Returns a configured AsyncClient. Caller is responsible for context-managing it.
    """
    ...
```

### `src/runner/classifier.py`

```python
from __future__ import annotations
from pathlib import Path

_pipeline = None  # module-level singleton

def get_classifier(model_path: Path | None = None):
    """
    Returns the loaded transformers pipeline (text-classification).
    On first call: loads from model_path (or settings.pair_classifier_path if None).
    Subsequent calls: returns cached pipeline regardless of model_path argument.
    Raises RuntimeError if model_path does not contain config.json.
    Thread-safe for reading (no mutation after first load).
    """
    global _pipeline
    ...

def score(text: str) -> tuple[bool, float]:
    """
    Runs the pair_classifier pipeline on text.
    Returns (jailbreak_success, unsafe_probability).
    jailbreak_success = (predicted_label == "LABEL_1" or == 1).
    """
    ...
```

### `src/runner/attack.py`

```python
from __future__ import annotations
import uuid

async def run_session(
    session: AsyncSession,
    model_name: str,
    source_filter: str | None,
    harm_category_filter: str | None,
    strategy_filter: str | None,
) -> uuid.UUID:
    """
    Creates a RunSession row, iterates over filtered attacks, fires each at Ollama,
    scores with pair_classifier, writes Run rows, closes session with aggregate stats,
    refreshes coverage_summary materialised view.
    Returns the session UUID.
    Logs progress every 10 attacks. Logs timeouts as warnings and skips the row
    (does not write a Run row for timed-out requests — no partial data).
    """
    ...

def main() -> None:
    """
    CLI entry point: uv run attack.
    Accepts --source, --harm-category, --strategy flags (all optional).
    Calls run_session, prints final session stats.
    """
    ...
```

### `src/api/main.py`

```python
from __future__ import annotations
from fastapi import FastAPI

def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application.
    Registers all routers.
    On startup: calls get_classifier() to force early load and fail fast.
    On startup: creates async DB engine and session factory, stores on app.state.
    """
    ...
```

### `src/api/deps.py`

```python
from __future__ import annotations
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an AsyncSession from the factory stored on app.state.
    Commits on clean exit, rolls back on exception.
    """
    ...
```

### Router: `src/api/routers/attacks.py`

```python
# GET /attacks
# Query params: page (int, default 1), page_size (int, default 50, max 200),
#               source (str | None), harm_category (str | None), strategy (str | None)
# Returns: AttackListOut
# SQL: SELECT ... FROM attacks WHERE (source = :source OR :source IS NULL) AND ...
#      ORDER BY created_at DESC LIMIT :page_size OFFSET (:page - 1) * :page_size

# GET /attacks/harm-categories
# Returns: FilterValuesOut (distinct harm_category values, sorted)
# SQL: SELECT DISTINCT harm_category FROM attacks ORDER BY 1

# GET /attacks/strategies
# Returns: FilterValuesOut (distinct strategy values, sorted)
# SQL: SELECT DISTINCT strategy FROM attacks ORDER BY 1
```

### Router: `src/api/routers/runs.py`

```python
# GET /runs
# Query params: session_id (uuid | None), page (int, default 1), page_size (int, default 50)
# Returns: RunListOut
# SQL: SELECT r.*, a.harm_category, a.strategy, a.attack_text
#      FROM runs r JOIN attacks a ON r.attack_id = a.id
#      WHERE (r.session_id = :session_id OR :session_id IS NULL)
#      ORDER BY r.created_at DESC LIMIT :page_size OFFSET ...

# GET /sample/{run_id}
# Path param: run_id (uuid)
# Returns: SampleOut
# SQL: SELECT r.*, a.harm_category, a.strategy, a.attack_text
#      FROM runs r JOIN attacks a ON r.attack_id = a.id WHERE r.id = :run_id
# Raises 404 if not found.
```

### Router: `src/api/routers/sessions.py`

```python
# GET /sessions
# No params.
# Returns: list[SessionOut]
# SQL: SELECT * FROM run_sessions ORDER BY created_at DESC
```

### Router: `src/api/routers/coverage.py`

```python
# GET /coverage
# No params. Queries coverage_summary materialised view.
# Returns: CoverageOut
# SQL: SELECT harm_category, strategy, total_runs, total_successes, asr
#      FROM coverage_summary ORDER BY harm_category, strategy
# Post-processes in Python: extract sorted unique harm_categories and strategies for axis labels.
```

### Router: `src/api/routers/strategy.py`

```python
# GET /strategy-comparison
# No params. Queries runs table directly (not materialised view — simpler, good enough).
# Returns: StrategyComparisonOut
# SQL: SELECT a.strategy,
#             COUNT(*) AS total_runs,
#             SUM(CASE WHEN r.jailbreak_success THEN 1 ELSE 0 END) AS total_successes,
#             AVG(r.jailbreak_success::int)::float AS asr
#      FROM runs r JOIN attacks a ON r.attack_id = a.id
#      GROUP BY a.strategy ORDER BY asr DESC
```

### Router: `src/api/routers/regression.py`

```python
# GET /regression
# No params.
# Returns: RegressionOut
# SQL: SELECT id, model_name, asr, total_attacks, created_at
#      FROM run_sessions ORDER BY created_at ASC
# Post-processes in Python: extract sorted unique model_names for legend.
```

---

## DB Schema (Migration SQL)

Full migration in `alembic/versions/001_initial_schema.py`. Equivalent DDL:

```sql
-- attacks
CREATE TABLE attacks (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source        VARCHAR(50)  NOT NULL,
    source_id     VARCHAR(200) NOT NULL,
    harm_category VARCHAR(100) NOT NULL,
    strategy      VARCHAR(100) NOT NULL,
    attack_text   TEXT         NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX uix_attacks_source_source_id ON attacks (source, source_id);
CREATE INDEX ix_attacks_harm_category ON attacks (harm_category);
CREATE INDEX ix_attacks_strategy ON attacks (strategy);

-- run_sessions
CREATE TABLE run_sessions (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name       VARCHAR(200) NOT NULL,
    total_attacks    INTEGER      NOT NULL DEFAULT 0,
    total_successes  INTEGER      NOT NULL DEFAULT 0,
    asr              FLOAT        NOT NULL DEFAULT 0.0,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_run_sessions_model_name ON run_sessions (model_name);
CREATE INDEX ix_run_sessions_created_at ON run_sessions (created_at);

-- runs
CREATE TABLE runs (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id        UUID         NOT NULL REFERENCES run_sessions(id),
    attack_id         UUID         NOT NULL REFERENCES attacks(id),
    model_name        VARCHAR(200) NOT NULL,
    response_text     TEXT         NOT NULL,
    jailbreak_success BOOLEAN      NOT NULL,
    classifier_score  FLOAT        NOT NULL,
    latency_ms        INTEGER      NOT NULL,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_runs_session_id ON runs (session_id);
CREATE INDEX ix_runs_attack_id ON runs (attack_id);
CREATE INDEX ix_runs_jailbreak_success ON runs (jailbreak_success);

-- coverage_summary materialised view
CREATE MATERIALIZED VIEW coverage_summary AS
SELECT
    a.harm_category,
    a.strategy,
    COUNT(*)                                          AS total_runs,
    SUM(CASE WHEN r.jailbreak_success THEN 1 ELSE 0 END) AS total_successes,
    AVG(r.jailbreak_success::int)::float             AS asr
FROM runs r
JOIN attacks a ON r.attack_id = a.id
GROUP BY a.harm_category, a.strategy;

CREATE UNIQUE INDEX uix_coverage_summary_category_strategy
    ON coverage_summary (harm_category, strategy);
```

The view refresh statement (called by `run_session()` at session close):
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY coverage_summary;
```

---

## Frontend Types (`web/src/types/index.ts`)

```typescript
export type Attack = {
  id: string
  source: string
  source_id: string
  harm_category: string
  strategy: string
  attack_text: string
  created_at: string
}

export type AttackListOut = {
  items: Attack[]
  total: number
  page: number
  page_size: number
}

export type Session = {
  id: string
  model_name: string
  total_attacks: number
  total_successes: number
  asr: number
  created_at: string
}

export type Run = {
  id: string
  session_id: string
  attack_id: string
  model_name: string
  response_text: string
  jailbreak_success: boolean
  classifier_score: number
  latency_ms: number
  created_at: string
  harm_category: string
  strategy: string
  attack_text: string
}

export type RunListOut = {
  items: Run[]
  total: number
  page: number
  page_size: number
}

export type SampleOut = {
  run_id: string
  attack_text: string
  response_text: string
  harm_category: string
  strategy: string
  jailbreak_success: boolean
  classifier_score: number
  latency_ms: number
  model_name: string
  session_id: string
  created_at: string
}

export type CoverageCell = {
  harm_category: string
  strategy: string
  total_runs: number
  total_successes: number
  asr: number
}

export type CoverageOut = {
  cells: CoverageCell[]
  harm_categories: string[]
  strategies: string[]
}

export type StrategyBar = {
  strategy: string
  total_runs: number
  total_successes: number
  asr: number
}

export type StrategyComparisonOut = {
  bars: StrategyBar[]
}

export type RegressionPoint = {
  session_id: string
  model_name: string
  asr: number
  total_attacks: number
  created_at: string
}

export type RegressionOut = {
  points: RegressionPoint[]
  model_names: string[]
}

export type FilterValuesOut = {
  values: string[]
}
```

---

## Frontend Hooks (`web/src/hooks/`)

```typescript
// useAttacks.ts
function useAttacks(params: {
  page: number
  pageSize: number
  source?: string
  harmCategory?: string
  strategy?: string
}): UseQueryResult<AttackListOut>
// refetchInterval: none (static data after seed)

// useAttackFilters.ts — populates dropdowns
function useHarmCategories(): UseQueryResult<FilterValuesOut>
function useStrategies(): UseQueryResult<FilterValuesOut>
// refetchInterval: none

// useSessions.ts
function useSessions(): UseQueryResult<Session[]>
// refetchInterval: 30_000 (sessions may be added by runner)

// useRuns.ts
function useRuns(params: {
  sessionId?: string
  page: number
  pageSize: number
}): UseQueryResult<RunListOut>
// refetchInterval: none

// useCoverage.ts
function useCoverage(): UseQueryResult<CoverageOut>
// refetchInterval: 30_000

// useStrategyComparison.ts
function useStrategyComparison(): UseQueryResult<StrategyComparisonOut>
// refetchInterval: 30_000

// useRegression.ts
function useRegression(): UseQueryResult<RegressionOut>
// refetchInterval: 30_000

// useSample.ts
function useSample(runId: string | null): UseQueryResult<SampleOut>
// refetchInterval: none; enabled: runId !== null
```

---

## Frontend Components

### `web/src/App.tsx`
Props: none. Renders a tab bar with five tabs (Attack Browser, Coverage Heatmap, Strategy Comparison, Regression Tracker, Sample Review). Uses React state for `activeTab`. Renders the active page component.

### `web/src/pages/AttackBrowser.tsx`
Props: none.
- State: `page`, `pageSize`, `sourceFilter`, `harmCategoryFilter`, `strategyFilter`, `selectedRunId`.
- Uses: `useAttacks(...)`, `useHarmCategories()`, `useStrategies()`.
- Renders: filter row (source text input — open-ended; harm_category dropdown from `useHarmCategories`; strategy dropdown from `useStrategies`); paginated table of attacks; on row click, sets `selectedRunId` and opens `SampleReview` modal or passes ID to the Sample Review tab.
- Note: source is a text input (two known values but not DB-enumerated via a dedicated endpoint — acceptable since the set is tiny and static).

### `web/src/pages/CoverageHeatmap.tsx`
Props: none.
- Uses: `useCoverage()`.
- Renders: `recharts ScatterChart` used as a heatmap. X axis: `harm_category` (categorical). Y axis: `strategy` (categorical). Each `CoverageCell` becomes a `Scatter` point with `x = harm_categories.indexOf(cell.harm_category)`, `y = strategies.indexOf(cell.strategy)`, custom `dot` rendered as a coloured square (use `Cell` with a linear colour scale: 0% ASR = green, 100% ASR = red, interpolated via a helper `asrToColour(asr: number): string`).
- Note: `ScatterChart` is the correct recharts approach for a 2D heatmap — there is no native `HeatmapChart` in recharts 2.x. The implementer uses `ScatterChart` with categorical axes and custom cell rendering.

### `web/src/pages/StrategyComparison.tsx`
Props: none.
- Uses: `useStrategyComparison()`.
- Renders: `recharts BarChart`. X axis: `strategy`. Y axis: `asr` (0–1 formatted as percentage). Bars sorted by `asr` descending. Tooltip shows `total_runs` and `total_successes`.

### `web/src/pages/RegressionTracker.tsx`
Props: none.
- Uses: `useRegression()`.
- Renders: `recharts LineChart`. X axis: `created_at` (ISO string, formatted as date). Y axis: `asr` (percentage). One `Line` per unique `model_name`. Uses `model_names` array from `RegressionOut` to render the legend. Points are `RegressionPoint` objects grouped by `model_name` in the component.

### `web/src/pages/SampleReview.tsx`
Props: none.
- State: `selectedSessionId` (uuid string | null), `selectedRunId` (uuid string | null).
- Uses: `useSessions()`, `useRuns({ sessionId: selectedSessionId, page, pageSize })`, `useSample(selectedRunId)`.
- Renders: session dropdown (populated from `useSessions()`); runs table filtered by session; on run row click, fetches and displays full sample: attack text in a code block, response text in a scrollable box, classifier label badge (green = safe, red = jailbreak), ASR score, latency.

---

## Dependencies (Import Graph)

```
src/config.py
    ← imported by: src/db.py, src/corpus/seed.py, src/runner/attack.py, src/api/main.py

src/db.py
    imports: src/config.py, src/models.py
    ← imported by: src/api/deps.py, src/corpus/seed.py, src/runner/attack.py

src/models.py
    imports: sqlalchemy (only)
    ← imported by: src/db.py, all routers, src/corpus/seed.py, src/runner/attack.py

src/corpus/constants.py
    imports: nothing
    ← imported by: src/corpus/loader.py

src/corpus/loader.py
    imports: src/corpus/constants.py, datasets (deferred)
    ← imported by: src/corpus/seed.py

src/corpus/seed.py
    imports: src/corpus/loader.py, src/db.py, src/models.py, src/config.py

src/runner/classifier.py
    imports: src/config.py, transformers (deferred)
    ← imported by: src/runner/attack.py, src/api/main.py (startup only)

src/runner/ollama_client.py
    imports: httpx
    ← imported by: src/runner/attack.py

src/runner/attack.py
    imports: src/runner/ollama_client.py, src/runner/classifier.py,
             src/db.py, src/models.py, src/config.py

src/api/deps.py
    imports: src/db.py
    ← imported by: all routers

src/api/schemas.py
    imports: pydantic (only)
    ← imported by: all routers

src/api/routers/*.py
    imports: src/api/deps.py, src/api/schemas.py, src/models.py

src/api/main.py
    imports: all routers, src/runner/classifier.py, src/db.py, src/config.py
```

No circular dependencies. `src/models.py` and `src/api/schemas.py` are pure — they import no project modules.

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Error handling (Python) | Specific exceptions with context. Router handlers let `HTTPException` propagate; unexpected exceptions caught at the FastAPI exception handler level and logged with `exc_info=True`. Runner loop catches `httpx.TimeoutException` per request — logs warning with attack ID, skips run row. All other exceptions in runner loop propagate to terminate the session. |
| Error handling (TypeScript) | TanStack Query handles loading/error states. Each page component renders an error message when `isError` is true. No thrown errors from components. |
| Configuration | Single `Settings` instance in `src/config.py` via pydantic-settings. All env vars read here. Fail fast on startup if required vars are missing (`PAIR_CLASSIFIER_PATH`, `DATABASE_URL`). |
| Logging | Python stdlib `logging`. Level: INFO in production, DEBUG for runner progress. Format: `%(asctime)s %(name)s %(levelname)s %(message)s`. Runner logs every 10 attacks at INFO; timeouts at WARNING with `exc_info=True`. API routers log at DEBUG only. |
| DB migrations | Alembic `upgrade head` on startup (called before app accepts traffic). Migration `001_initial_schema.py` creates all tables, indexes, and the materialised view. |
| CORS | FastAPI `CORSMiddleware` allows `http://localhost:5173` (Vite dev server). Configurable via `ALLOWED_ORIGINS` env var. |
| Testing (Python) | pytest-asyncio with `asyncio_mode = "auto"`. `conftest.py` provides: async engine with test DB, session fixture, seeded `Attack` and `RunSession` + `Run` rows. All HuggingFace calls mocked via `pytest-mock`. Ollama calls mocked via `pytest-httpserver`. Classifier calls mocked via `pytest-mock` patching `transformers.pipeline`. |
| Testing (TypeScript) | vitest + MSW. `src/test/handlers.ts` defines MSW handlers for all 7 API endpoints. `src/test/setup.ts` starts the MSW server before tests. Each page component test: renders component, asserts visible content against mocked data, asserts loading state. |

---

## Implementation Notes

### Dataset Loading (corpus/loader.py)

1. **JailbreakBench schema:** As of 2024, `JailbreakBench/JailbreakBench` has a `behaviors` split containing rows with `Behavior` (goal text), `Category` (harm_category), and `Jailbreaks` (list of dicts with `method` and `prompt` keys). The constants file uses the exact field names — if they differ on first `datasets.load_dataset()` call, the implementer should inspect with `dataset[0].keys()` and update constants accordingly. Do not hardcode field names outside `constants.py`.
2. **AdvBench schema:** `llm-attacks/advbench` has `harmful_behaviors` and `harmful_strings` subsets. Load `harmful_behaviors`, which has `goal` and `target` columns. Only `goal` is used.
3. **Offline caching:** `datasets` caches to `~/.cache/huggingface/datasets` after first pull. No special configuration needed. The `seed-corpus` CLI will work offline after the first run.
4. **Upsert pattern:** Use SQLAlchemy `insert(...).on_conflict_do_nothing(index_elements=["source", "source_id"])` for idempotent seeding. Do not DELETE+INSERT — preserves existing `attack_id` references in `runs`.

### Ollama Client (runner/ollama_client.py)

The Ollama `/api/chat` endpoint (not `/v1/chat/completions`). Request body:
```json
{
  "model": "<model_name>",
  "messages": [{"role": "user", "content": "<attack_text>"}],
  "stream": false
}
```
Response body: `{"message": {"role": "assistant", "content": "..."}, ...}`. Extract `response["message"]["content"]`.

### pair_classifier Inference (runner/classifier.py)

The `pair_classifier` checkpoint is a DistilBERT binary classifier fine-tuned with HuggingFace `Trainer`. Load with:
```python
from transformers import pipeline
pipe = pipeline("text-classification", model=str(model_path), device=-1)
```
`device=-1` forces CPU — the classifier is small, CPU inference is fast enough (~10–50ms). Output: list of `[{"label": "LABEL_0" | "LABEL_1", "score": float}]`. `LABEL_1` = unsafe. `jailbreak_success = (result[0]["label"] == "LABEL_1")`. `classifier_score = result[0]["score"] if jailbreak_success else 1 - result[0]["score"]` — always the unsafe class probability.

### coverage_summary Refresh

The `REFRESH MATERIALIZED VIEW CONCURRENTLY coverage_summary` statement requires the unique index to exist before the first refresh. The first refresh after the migration runs non-concurrently (the `CONCURRENTLY` keyword requires the view to be non-empty — the first refresh can be a plain `REFRESH`). The runner should do: plain `REFRESH` if view is empty, `REFRESH CONCURRENTLY` otherwise. Simplest approach: always use plain `REFRESH` in v1 — `CONCURRENTLY` matters only under read load, and this is a local dev tool.

Decision: **use plain `REFRESH MATERIALIZED VIEW coverage_summary`** in v1. The `CONCURRENTLY` flag can be added in v2. This avoids the empty-view edge case entirely.

### ScatterChart Heatmap (CoverageHeatmap.tsx)

recharts does not have a native HeatmapChart. Use `ScatterChart` with categorical axes:
```tsx
import { ScatterChart, Scatter, XAxis, YAxis, Cell, Tooltip } from 'recharts'

// harmCategories and strategies are sorted string arrays from CoverageOut
// Map category/strategy to numeric index for scatter positioning
const data = cells.map(cell => ({
  x: harmCategories.indexOf(cell.harm_category),
  y: strategies.indexOf(cell.strategy),
  asr: cell.asr,
  ...cell,
}))

function asrToColour(asr: number): string {
  // Linear interpolation: 0 = hsl(120, 70%, 45%) green, 1 = hsl(0, 70%, 45%) red
  const hue = Math.round(120 * (1 - asr))
  return `hsl(${hue}, 70%, 45%)`
}

<ScatterChart width={800} height={400}>
  <XAxis type="number" dataKey="x" ticks={harmCategories.map((_, i) => i)}
         tickFormatter={(i) => harmCategories[i] ?? ''} />
  <YAxis type="number" dataKey="y" ticks={strategies.map((_, i) => i)}
         tickFormatter={(i) => strategies[i] ?? ''} />
  <Scatter data={data} shape="square">
    {data.map((entry, idx) => (
      <Cell key={idx} fill={asrToColour(entry.asr)} />
    ))}
  </Scatter>
  <Tooltip content={({ payload }) => { /* render harm_category, strategy, asr, total_runs */ }} />
</ScatterChart>
```

### Regression Tracker Line Grouping

`RegressionOut.points` is a flat list ordered by `created_at`. The `LineChart` needs one series per model. In the component:
```tsx
const seriesByModel = Object.fromEntries(
  modelNames.map(name => [name, points.filter(p => p.model_name === name)])
)
// Render one <Line> per modelNames entry, dataKey="asr", data={seriesByModel[name]}
```

### .env.example (backend)

```
DATABASE_URL=postgresql+asyncpg://redteam:redteam@localhost:5435/redteam
PAIR_CLASSIFIER_PATH=/path/to/muppet-labs/resources/models/llm-safety-monitor/pair_classifier
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
OLLAMA_TIMEOUT_S=120
ALLOWED_ORIGINS=http://localhost:5173
```

### .env.example (frontend, web/)

```
VITE_API_URL=http://localhost:8000
```

### pyproject.toml scripts block

```toml
[tool.uv.scripts]
seed-corpus = "src.corpus.seed:main"
attack = "src.runner.attack:main"
api = "uvicorn src.api.main:create_app --factory --reload --port 8000"
```

### Postgres Docker Compose

The implementer adds a `docker-compose.yml` at the project root:
```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: redteam
      POSTGRES_PASSWORD: redteam
      POSTGRES_DB: redteam
    ports:
      - "5435:5432"
    volumes:
      - redteam_pgdata:/var/lib/postgresql/data
volumes:
  redteam_pgdata:
```

---

## Handoff

**Next role:** implementer

The implementer opens this file and begins coding. All design decisions are resolved. No open questions remain.

**Implementation order (avoid dependency issues):**
1. `pyproject.toml` + `.env` + `docker-compose.yml` — project scaffold
2. `src/models.py` + `src/config.py` + `src/db.py` — data layer with no dependencies
3. Alembic migration `001_initial_schema.py` — run `alembic upgrade head` to validate
4. `src/corpus/constants.py` + `src/corpus/loader.py` + `src/corpus/seed.py` — corpus seeder
5. `src/runner/classifier.py` + `src/runner/ollama_client.py` + `src/runner/attack.py` — runner
6. `src/api/schemas.py` + `src/api/deps.py` + all routers + `src/api/main.py` — API
7. `web/` scaffold (Vite, TanStack Query, shadcn/ui) → `types/index.ts` → hooks → page components
8. pytest suite (mocked external calls) → vitest suite (MSW)

**Flags for implementer:**
- Inspect the JailbreakBench dataset field names before writing loader code. The constants in `constants.py` are based on published schema; verify against actual `dataset[0].keys()` output and update constants if needed.
- The `coverage_summary` view must be refreshed with plain `REFRESH` (not `CONCURRENTLY`) in v1. Do not add the `CONCURRENTLY` keyword until the view-is-empty edge case is handled.
- `asrToColour` must handle `asr = 0.0` (all runs safe) without crashing. `Math.round(120 * 1) = 120` (green) — correct.
- `transformers.pipeline` import is deferred inside `get_classifier()` to avoid slow import at CLI startup for non-classifier commands (e.g. `seed-corpus`).
- All test DB fixtures use a separate test database (e.g. `redteam_test` on port 5435). The `conftest.py` overrides `DATABASE_URL` via pytest fixture scope.
