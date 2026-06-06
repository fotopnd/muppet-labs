# Architect Output — multi-turn-safety-monitor

**Role:** architect
**Sequence:** `new-project-full` (step 3)
**Date:** 2026-06-06

---

## System Overview

The multi-turn-safety-monitor is a two-process system: a FastAPI backend (`api/`) and a Vite/React SPA (`web/`). The API owns a PostgreSQL database (port 5437) and exposes all read/write endpoints. On `POST /conversations`, the API persists the conversation and turns, then synchronously scores each user turn via a DistilBERT wrapper (`classifier.py`) and computes the escalation analysis via `analyzer.py`, before returning `ConversationDetail`. The classifier is loaded once at startup in the FastAPI lifespan context manager. The seed script (`seed.py`) is a CLI entry point in the same uv project that reads from `tests/fixtures/conversations.json` and calls the same ORM layer directly (not via HTTP). The React SPA polls the API via TanStack Query and renders a 4-tab dashboard.

Data flow: `POST /conversations` → `classifier.py` (per user turn) → `analyzer.py` (escalation + pattern) → Postgres (`conversations`, `turns`, `conversation_analyses`) → FastAPI read endpoints → React dashboard.

---

## Open Questions Resolved

**OQ1 — Synchronous scoring on ingest:**
Confirmed. The classifier is loaded once in lifespan; each request calls `classifier.score(text)` which is a model forward pass only (~5–10ms on MPS per turn). For a 20-turn conversation, total scoring overhead is ~100–200ms — acceptable for a demo tool. No background queue needed.

**OQ2 — reanalyze re-scores all user turns:**
Confirmed. `POST /conversations/{id}/reanalyze` re-scores ALL user turns (overwriting existing scores) and recomputes the `ConversationAnalysis`. This allows re-analysis if the checkpoint or threshold changes. Existing `ConversationAnalysis` is deleted and re-created, not updated in place.

**OQ3 — SQLAlchemy relationship loading strategy:**
- `GET /conversations` (list): load conversations only, no relationship loading — `turn_count` is a persisted column, not a relationship count.
- `GET /conversations/{id}` (detail): `selectinload(Conversation.turns)` + `selectinload(Conversation.analysis)`. Two extra queries, no N+1.
- Seed and reanalyze: use `session.execute(select(Turn).where(Turn.conversation_id == id))` directly — no relationship traversal.

**OQ4 — escalation_score clamping:**
Confirmed. After computing `(max * 0.4) + (trend * 0.4) + (mean * 0.2)`, clamp to `[0.0, 1.0]` via `max(0.0, min(1.0, score))`. `score_trend` can be negative (decreasing scores), which is fine — it reduces the escalation_score below the max/mean contribution.

**OQ5 — Pattern filter SQL:**
`WHERE pattern = :pattern` is sufficient. Pattern is only non-null on escalating conversations (set by design in `analyzer.py`). No need to also filter on `status = 'escalating'` — pattern nullability implies status. But filtering on both is also correct and explicit; the implementer may add `AND status = 'escalating'` for clarity.

**OQ6 (new) — numpy for slope computation:**
Use `numpy.polyfit(range(n), scores, 1)[0]` for slope. Add `numpy` as an explicit dependency in `pyproject.toml`. NumPy is already a transitive dependency of `torch`/`transformers` but must be declared explicitly per workspace convention.

---

## Data Models

### SQLAlchemy ORM (`models.py`)

```python
class ConversationStatus(StrEnum):
    pending = "pending"
    clean = "clean"
    flagged = "flagged"
    escalating = "escalating"

class TurnRole(StrEnum):
    user = "user"
    assistant = "assistant"

class EscalationPattern(StrEnum):
    foot_in_door = "foot_in_door"
    persona_hijack = "persona_hijack"
    context_reset = "context_reset"
    goal_hijack = "goal_hijack"
    incremental_harm = "incremental_harm"

class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    system_prompt: Mapped[str] = mapped_column(Text)
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus, native_enum=False),
        default=ConversationStatus.pending,
        index=True,
    )
    turn_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    analyzed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    turns: Mapped[list["Turn"]] = relationship(back_populates="conversation")
    analysis: Mapped["ConversationAnalysis | None"] = relationship(
        back_populates="conversation", uselist=False
    )

class Turn(Base):
    __tablename__ = "turns"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id"), index=True)
    turn_index: Mapped[int]
    role: Mapped[TurnRole] = mapped_column(Enum(TurnRole, native_enum=False))
    content: Mapped[str] = mapped_column(Text)
    toxicity_score: Mapped[float | None] = mapped_column(nullable=True)
    flagged: Mapped[bool] = mapped_column(default=False)
    scored_at: Mapped[datetime | None] = mapped_column(nullable=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="turns")

class ConversationAnalysis(Base):
    __tablename__ = "conversation_analyses"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id"), unique=True, index=True
    )
    escalation_score: Mapped[float]
    score_trend: Mapped[float]
    max_turn_score: Mapped[float]
    mean_turn_score: Mapped[float]
    peak_turn_index: Mapped[int | None] = mapped_column(nullable=True)
    escalation_pattern: Mapped[EscalationPattern | None] = mapped_column(
        Enum(EscalationPattern, native_enum=False), nullable=True
    )
    analyzed_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    conversation: Mapped["Conversation"] = relationship(back_populates="analysis")
```

### Pydantic Schemas (`schemas.py`)

```python
class TurnCreate(BaseModel):
    role: TurnRole
    content: str

class ConversationCreate(BaseModel):
    system_prompt: str
    turns: list[TurnCreate]
    model_config = ConfigDict(str_strip_whitespace=True)

class TurnDetail(BaseModel):
    id: UUID
    turn_index: int
    role: TurnRole
    content: str
    toxicity_score: float | None
    flagged: bool

class AnalysisDetail(BaseModel):
    escalation_score: float
    score_trend: float
    max_turn_score: float
    mean_turn_score: float
    peak_turn_index: int | None
    escalation_pattern: EscalationPattern | None
    analyzed_at: datetime

class ConversationDetail(BaseModel):
    id: UUID
    system_prompt: str
    status: ConversationStatus
    turn_count: int
    created_at: datetime
    analyzed_at: datetime | None
    turns: list[TurnDetail]
    analysis: AnalysisDetail | None

class ConversationListItem(BaseModel):
    id: UUID
    status: ConversationStatus
    turn_count: int
    escalation_pattern: EscalationPattern | None  # from joined analysis
    created_at: datetime

class DailyCount(BaseModel):
    date: str           # YYYY-MM-DD
    count: int

class MetricsResponse(BaseModel):
    total_conversations: int
    status_breakdown: dict[str, int]
    pattern_breakdown: dict[str, int]
    escalation_rate: float
    daily_ingested_30d: list[DailyCount]

class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
```

---

## Module Interfaces

### `classifier.py`

```python
class ToxicityClassifier:
    """Singleton wrapper around the fine-tuned DistilBERT checkpoint."""

    def __init__(self, checkpoint_dir: Path) -> None:
        """Loads model and tokeniser from checkpoint_dir. Raises RuntimeError if dir missing."""
        ...

    def score(self, text: str) -> float:
        """Returns probability of positive class (toxicity) in [0, 1]."""
        ...

# Module-level instance, set during FastAPI lifespan
_classifier: ToxicityClassifier | None = None

def get_classifier() -> ToxicityClassifier:
    """Returns the module-level instance. Raises RuntimeError if not initialised."""
    if _classifier is None:
        raise RuntimeError("Classifier not initialised — call init_classifier() first.")
    return _classifier

def init_classifier(checkpoint_dir: Path) -> ToxicityClassifier:
    """Called once during lifespan. Sets module-level _classifier."""
    ...
```

The FastAPI lifespan calls `init_classifier(settings.model_checkpoint_dir)`. Route handlers call `get_classifier()` via a `Depends` wrapper or inline. No SQLAlchemy-style session injection needed — the classifier is truly a singleton with no per-request state.

### `analyzer.py`

```python
@dataclass
class ScoredTurn:
    turn_index: int
    role: TurnRole
    content: str
    toxicity_score: float  # user turns only; assistant turns excluded before passing in

@dataclass
class AnalysisResult:
    escalation_score: float
    score_trend: float
    max_turn_score: float
    mean_turn_score: float
    peak_turn_index: int | None
    status: ConversationStatus
    escalation_pattern: EscalationPattern | None

def compute_slope(scores: list[float]) -> float:
    """Returns linear slope via numpy.polyfit. Returns 0.0 if len(scores) < 2."""
    ...

def classify_pattern(
    turns: list[ScoredTurn],
    score_trend: float,
    user_scores: list[float],
) -> EscalationPattern | None:
    """Returns first matching pattern or None. Rules applied in priority order."""
    ...

def analyze(
    turns: list[ScoredTurn],
    escalation_threshold: float,
    flag_threshold: float,
) -> AnalysisResult:
    """
    Main entry point. Accepts only user turns (caller filters to role==user).
    Returns AnalysisResult with all computed fields.
    """
    ...
```

### `routers/conversations.py`

```python
router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.post("/", status_code=201, response_model=ConversationDetail)
async def create_conversation(
    body: ConversationCreate,
    db: AsyncSession = Depends(get_db),
) -> ConversationDetail: ...

@router.get("/", response_model=Page[ConversationListItem])
async def list_conversations(
    status: ConversationStatus | None = None,
    pattern: EscalationPattern | None = None,
    page: int = 1,
    page_size: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
) -> Page[ConversationListItem]: ...

@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ConversationDetail: ...

@router.post("/{conversation_id}/reanalyze", response_model=ConversationDetail)
async def reanalyze_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ConversationDetail: ...
```

### `routers/metrics.py`

```python
router = APIRouter(tags=["metrics"])

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(db: AsyncSession = Depends(get_db)) -> MetricsResponse: ...

@router.get("/health")
async def health() -> dict[str, str]: ...
```

---

## Dependencies

```
classifier.py        ← torch, transformers, pathlib.Path
analyzer.py          ← numpy, models.py (enums only, no DB)
models.py            ← sqlalchemy, stdlib
schemas.py           ← pydantic, models.py (enums only)
database.py          ← sqlalchemy, config.py
config.py            ← pydantic-settings
routers/conversations.py ← schemas, models, database, classifier, analyzer
routers/metrics.py   ← schemas, models, database
main.py              ← all routers, database, classifier (lifespan), config
seed.py              ← models, database, fixtures JSON
```

No circular dependencies. `analyzer.py` imports enums from `models.py` only (no ORM classes) — keeps it testable without a DB.

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Error handling | HTTPException for 404/422; `RuntimeError` in classifier and analyzer for uninitialised state; no broad `except Exception` except in lifespan teardown |
| Configuration | `pydantic-settings` `Settings` class; `extra="ignore"` for shared .env with VITE_* vars; `MODEL_CHECKPOINT_DIR`, `DATABASE_URL`, `TEST_DATABASE_URL`, `ESCALATION_THRESHOLD` (default 0.6), `FLAG_THRESHOLD` (default 0.7) |
| Logging | `logging` stdlib; `logger = logging.getLogger(__name__)` per module; `exc_info=True` at exception boundaries |
| Testing | Integration: `AsyncSession` against `TEST_DATABASE_URL` Postgres; `create_all` in conftest; `AsyncClient` via `httpx`. Unit: `analyzer.py` and `classifier.score()` (mock torch model). The metrics test asserts computed `escalation_rate` and `pattern_breakdown` values with seeded data, not just response shape. |
| DB init | `create_all` in lifespan for simplicity (no Alembic for v1); same pattern as other workspace projects that don't run migrations in the demo. |

---

## Implementation Notes for Implementer

1. **Classifier singleton pattern:** `init_classifier()` sets `_classifier` at module level. `get_classifier()` checks for `None` and raises `RuntimeError`. The lifespan does: `classifier_module.init_classifier(settings.model_checkpoint_dir)`. Route handlers call `get_classifier()` directly (not via `Depends`) since it has no async or per-request state.

2. **Scoring in create_conversation:** After persisting all turns, iterate over user turns in turn_index order, call `classifier.score(turn.content)`, update `turn.toxicity_score = score`, `turn.flagged = (score >= settings.flag_threshold)`, `turn.scored_at = datetime.now(UTC)`. Then pass scored user turns to `analyzer.analyze()`. Persist `ConversationAnalysis`. Update `conversation.status` and `conversation.analyzed_at`.

3. **ConversationListItem pattern field:** The list endpoint must LEFT JOIN `conversation_analyses` to include `escalation_pattern` on each item. Use SQLAlchemy `.outerjoin()` with `.options(contains_eager(...))` or a raw `select` with explicit column aliasing. Do not issue a separate query per conversation row.

4. **NumPy polyfit edge case:** When `len(user_scores) == 0`, return `mean=0.0`, `max=0.0`, `trend=0.0`, `escalation_score=0.0`, `status=clean`, `pattern=None`. When `len(user_scores) == 1`, slope is 0.0 (insufficient data for a trend).

5. **Pattern rules are case-insensitive:** All keyword matching in `classify_pattern()` uses `content.lower()` before checking substrings.

6. **Fixtures file format** (`tests/fixtures/conversations.json`): a JSON array of conversation objects matching the `ConversationCreate` schema. The seed script reads this file and creates each conversation via the ORM (bypassing the HTTP layer so it does not depend on the API being up).

7. **VITE_API_URL in .env.example:** must be added in the same implementer pass as the React SPA. Default: `http://localhost:8000`.

8. **Postgres docker-compose.yml port:** `5437:5432`. The API connects on port 5437 from the host.

---

## Handoff

**Next role:** design-brief (if this sequence includes frontend planning), or directly to implementer (if the dashboard layout is straightforward enough to proceed from these specs).

Given that the 4-tab layout is analogous to other workspace projects (same shadcn/ui + recharts stack, same TanStack Query patterns), the frontend-architect step can be skipped. The implementer reads this file and the planner output and proceeds directly to implementation.

**Flags for implementer:**
- Confirm `resources/models/toxicity-classifier-finetuned/distilbert-best` exists and has `config.json` before writing classifier loading code. If missing, seed the path from `.env` and document the prerequisite.
- The `Conversation.analysis` relationship is `uselist=False` — verify SQLAlchemy does not require `lazy="select"` vs `lazy="joined"` to work correctly with `selectinload`.
- `numpy.polyfit` returns the slope as `coeffs[0]` (highest degree first). Confirm with a quick sanity check in `test_analyzer.py`: `compute_slope([0.1, 0.3, 0.5])` should be approximately `0.2`.
