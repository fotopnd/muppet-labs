# Architect Output — Year Zero Game

**Sequence:** `new-project-full` | **Role:** architect | **Step:** 3 of 9  
**Date:** 2026-06-15  
**Reads:** `roles/planner/output/output.md`, `resources/data-schema.md`, `resources/system-architecture.md`, `resources/game-mechanics.md`, `resources/content-design.md`

---

## Open Questions Resolved

**Q1 — SSE broadcast:** `asyncio.Queue` per client confirmed. `app.state.sse_queues: list[asyncio.Queue]`. On `/decisions/batch` commit, push sentinel `"refresh"` to all queues. Each generator wakes, recomputes aggregate via SQL, yields event. On disconnect: generator catches `GeneratorExit`, removes its queue from the list.

**Q2 — Swipe gesture:** `@use-gesture/react` `useDrag` confirmed. Commit threshold: `Math.abs(dx) > cardRef.current.offsetWidth * 0.3`.

**Q3 — Pixel aesthetic:** CSS approximation confirmed for v1. `image-rendering: pixelated` on card/sprite elements. Stamp animation: 3-frame CSS `@keyframes`. Status bars: `background: linear-gradient(to right, <barColour> <pct>%, #1e1e1e <pct>%)`.

**Q4 — Category tier state:** `localStorage` for interim. `PATCH /sessions/{id}` for permanent record at game end.

**Q5 — Phase trigger authority:** Client-side confirmed.

**Q6 — MVP seed fixture composition (30 cards):**
- 10 cards: `sovereign_verdict = NULL`, `phase = 1` — calibration block (always no-agent, Day 1 only)
- 8 cards: `generation_tier = 1`, phases 1–2 — strongly inverted tier-1 verdicts
- 6 cards: `generation_tier = 2`, phases 1–2 — partially corrected tier-2 verdicts  
- 6 cards: `generation_tier = 3`, phases 2–3 — mostly correct tier-3 verdicts
- Harm categories: violence, hate_speech, pii_exposure, cybercrime, sexual_content (5 categories, 6 cards each)
- `is_harmful` split: 50/50 (15 harmful, 15 benign)
- `target_condition_mix` for all phase cards: `{"none": 0.25, "tier_1": 0.25, "tier_2": 0.25, "tier_3": 0.25}`
- Calibration cards: `target_condition_mix = {"none": 1.0, ...}` (always served as no-agent)

---

## System Overview

The Year Zero backend is a single FastAPI app (port 8005) backed by PostgreSQL (port 5437). It has four routers: sessions, decisions, cards, analytics. The decisions router is the write-hot path — it inserts `player_decisions` rows and broadcasts an SSE refresh signal to all connected analytics subscribers. The cards router implements server-side condition assignment, maintaining balanced cross-player experimental conditions without client involvement. The analytics router serves both a one-shot summary endpoint and a persistent SSE stream for the live dashboard. The frontend is two routes: `/` (game) and `/analytics` (live charts). All game state — bars, phase, day, pending decisions, category tiers — lives in a client-side `useReducer`. No backend calls during active card play; only at session start, end-of-day batch submit, phase unlock, and game over.

---

## Data Models

### Backend ORM (SQLAlchemy 2 async)

```python
# year_zero/models.py

class DocumentLibrary(Base):
    __tablename__ = "document_library"
    id: Mapped[int] = mapped_column(primary_key=True)
    prompt_text: Mapped[str]
    document_text: Mapped[str]
    generation_model: Mapped[str]          # 'gemma2:9b' | 'qwen2.5:7b' | 'llama3.1:8b'
    generation_tier: Mapped[int]           # 1 | 2 | 3  CHECK (1-3)
    strategy: Mapped[str]
    harm_category: Mapped[str]
    is_harmful: Mapped[bool]
    phase: Mapped[int]                     # 1 | 2 | 3  CHECK (1-3)
    sovereign_verdict: Mapped[bool | None]       # NULL = no-agent card
    sovereign_confidence: Mapped[float | None]
    sovereign_reasoning: Mapped[str | None]
    verdict_correct: Mapped[bool | None]         # NULL when sovereign_verdict is NULL
    target_condition_mix: Mapped[dict] = mapped_column(JSONB, ...)
    served_none: Mapped[int] = mapped_column(default=0)
    served_tier_1: Mapped[int] = mapped_column(default=0)
    served_tier_2: Mapped[int] = mapped_column(default=0)
    served_tier_3: Mapped[int] = mapped_column(default=0)

class GameSession(Base):
    __tablename__ = "game_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    ended_at: Mapped[datetime | None]
    total_days: Mapped[int | None]
    total_decisions: Mapped[int | None]
    correct_decisions: Mapped[int | None]
    accuracy: Mapped[float | None]
    phase_reached: Mapped[int | None]
    game_over_condition: Mapped[str | None]   # 'TRUST_ZERO'|'SECURITY_MAX'|'TREASURY_ZERO'|'LEGITIMACY_ZERO'|'COMPLIANCE_MAX'|'COMPLIANCE_ZERO'
    final_bar_public_trust: Mapped[int | None]
    final_bar_security: Mapped[int | None]
    final_bar_treasury: Mapped[int | None]
    final_bar_legitimacy: Mapped[int | None]
    final_bar_compliance: Mapped[int | None]
    total_agreements: Mapped[int | None]
    total_overrides: Mapped[int | None]
    total_no_agent_decisions: Mapped[int | None]
    agreement_rate: Mapped[float | None]
    correct_agreements: Mapped[int | None]
    correct_overrides: Mapped[int | None]
    correct_no_agent: Mapped[int | None]
    calibration_accuracy: Mapped[float | None]
    calibration_decisions: Mapped[int | None]
    category_tiers: Mapped[dict | None] = mapped_column(JSONB)

class PlayerDecision(Base):
    __tablename__ = "player_decisions"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id"))
    document_id: Mapped[int] = mapped_column(ForeignKey("document_library.id"))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    agent_condition: Mapped[str]           # 'none'|'tier_1'|'tier_2'|'tier_3'
    player_verdict: Mapped[str]            # 'CLEAR'|'REDACT'|'ESCALATE'  CHECK
    player_correct: Mapped[bool]
    latency_ms: Mapped[float]
    agreed_with_agent: Mapped[bool | None]  # NULL when agent_condition='none'
    bar_public_trust: Mapped[int]
    bar_security: Mapped[int]
    bar_treasury: Mapped[int]
    bar_legitimacy: Mapped[int]
    bar_compliance: Mapped[int]
    game_day: Mapped[int]
    phase: Mapped[int]
    category_tier: Mapped[int]
    is_calibration: Mapped[bool] = mapped_column(default=False)
```

Indexes: `player_decisions(session_id)`, `player_decisions(document_id)`, `player_decisions(agent_condition)`, `player_decisions(player_correct)`, `player_decisions(created_at)`, `document_library(strategy)`, `document_library(harm_category)`, `document_library(generation_model)`, `document_library(phase)`, `document_library(is_harmful)`.

---

## Module Interfaces

### `year_zero/api/schemas.py`

```python
# Requests
class CreateSessionRequest(BaseModel):
    started_at: datetime

class DecisionItem(BaseModel):
    document_id: int
    agent_condition: Literal["none", "tier_1", "tier_2", "tier_3"]
    player_verdict: Literal["CLEAR", "REDACT", "ESCALATE"]
    player_correct: bool
    latency_ms: float
    agreed_with_agent: bool | None
    bars: dict[str, int]           # {"public_trust": N, "security": N, ...}
    game_day: int
    phase: int
    category_tier: int
    is_calibration: bool

class BatchDecisionsRequest(BaseModel):
    session_id: int
    game_day: int
    decisions: list[DecisionItem]

class PatchSessionRequest(BaseModel):
    ended_at: datetime
    total_days: int
    total_decisions: int
    correct_decisions: int
    accuracy: float
    phase_reached: int
    game_over_condition: str
    final_bars: dict[str, int]
    compliance_profile: dict[str, int | float]
    calibration_accuracy: float
    calibration_decisions: int
    category_tiers: dict[str, int]

# Responses
class SessionCreated(BaseModel):
    session_id: int

class BatchAccepted(BaseModel):
    accepted: int

class CardOut(BaseModel):
    id: int
    document_text: str
    harm_category: str
    phase: int
    generation_tier: int
    is_harmful: bool                       # included so client can score locally for bar updates
    sovereign_verdict: bool | None
    sovereign_confidence: float | None
    sovereign_reasoning: str | None
    agent_condition: Literal["none", "tier_1", "tier_2", "tier_3"]

class AnalyticsSummary(BaseModel):
    total_sessions: int
    sessions_today: int
    global_fp_rate: float                  # player CLEARed harmful doc (false negative in safety terms)
    global_fn_rate: float                  # player REDACTed benign doc (false positive)
    avg_latency_ms: float
    phase_survival: dict[str, float]       # {"phase_1": 1.0, "phase_2": 0.4, "phase_3": 0.1}
    system_drift_error_rate: list[dict]    # [{date: str, error_rate: float}] last 30 sessions

class UpliftRow(BaseModel):
    document_id: int
    strategy: str
    harm_category: str
    generation_model: str
    is_harmful: bool
    no_agent_decisions: int
    no_agent_accuracy: float
    agent_decisions: int
    agent_accuracy: float
    document_uplift: float
```

### `year_zero/api/routers/cards.py`

```python
def assign_condition(doc: DocumentLibrary) -> str:
    """
    Returns the agent_condition to assign for this document on this serve.
    Picks the condition most under-served relative to target_condition_mix.
    For calibration cards (sovereign_verdict is None), always returns 'none'.
    """
    if doc.sovereign_verdict is None:
        return "none"
    served = {
        "none": doc.served_none,
        "tier_1": doc.served_tier_1,
        "tier_2": doc.served_tier_2,
        "tier_3": doc.served_tier_3,
    }
    target: dict[str, float] = doc.target_condition_mix
    total = sum(served.values()) or 1
    deficit = {c: target.get(c, 0.0) - (served[c] / total) for c in target}
    return max(deficit, key=deficit.get)

# GET /cards/calibration
# Returns: list[CardOut] (10 cards, sovereign_verdict=NULL, phase=1)
# After serving: increments served_none on each document

# GET /cards/phase/{phase}?category_tiers=<JSON>
# category_tiers: dict[str, int] — player's current tier per harm_category
# Filters: document_library.phase == phase
# For each doc: assign_condition() → picks condition → increments served_* counter
# Returns: list[CardOut] with agent_condition set per doc
# Note: cards are returned as a pool (not a pre-shuffled sequence); client draws from the pool
```

### `year_zero/api/routers/decisions.py`

```python
# POST /decisions/batch
# After inserting all player_decisions rows:
# → for q in request.app.state.sse_queues: await q.put("refresh")
# Returns: BatchAccepted(accepted=len(decisions))
```

### `year_zero/api/routers/analytics.py`

```python
# GET /analytics/summary → AnalyticsSummary (single SQL query or CTE)

# GET /analytics/stream → StreamingResponse (SSE)
# On connect: create asyncio.Queue(); append to app.state.sse_queues
# Loop: await q.get() → "refresh" sentinel → recompute summary → yield SSE event
# On disconnect (GeneratorExit): remove q from app.state.sse_queues

# GET /analytics/uplift → list[UpliftRow]
# SQL: document-level uplift query from data-schema.md §Key Analytics Queries, Query 7
# HAVING condition: ≥5 decisions in each condition bucket
```

### `year_zero/api/main.py`

```python
# app.state.sse_queues: list[asyncio.Queue] = []
# Lifespan: await init_db(engine); app.state.sse_queues = []
# CORS: allow_origins=["http://localhost:5175", VITE_ORIGIN from env]
# Router prefixes: /sessions, /decisions, /cards, /analytics
# Register /cards/calibration BEFORE /cards/{phase} to avoid catch-all shadowing
```

### `year_zero/config.py`

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+asyncpg://..."
    ollama_url: str = "http://localhost:11434"
    vite_origin: str = "http://localhost:5175"
    api_port: int = 8005
```

---

## Frontend — `useGameState` Reducer

### State Shape

```typescript
// src/types/index.ts
type Verdict = 'CLEAR' | 'REDACT' | 'ESCALATE'
type AgentCondition = 'none' | 'tier_1' | 'tier_2' | 'tier_3'
type GameOverReason = 'TRUST_ZERO' | 'SECURITY_MAX' | 'TREASURY_ZERO' | 'LEGITIMACY_ZERO' | 'COMPLIANCE_MAX' | 'COMPLIANCE_ZERO'

interface BarState {
  publicTrust: number    // starts 60
  security: number       // starts 20
  treasury: number       // starts 80
  legitimacy: number     // starts 70
  compliance: number     // starts 50
}

interface Card {
  id: number
  documentText: string
  harmCategory: string
  phase: number
  generationTier: number
  isHarmful: boolean
  sovereignVerdict: boolean | null
  sovereignConfidence: number | null
  sovereignReasoning: string | null
  agentCondition: AgentCondition
}

interface PendingDecision {
  documentId: number
  agentCondition: AgentCondition
  playerVerdict: Verdict
  playerCorrect: boolean
  latencyMs: number
  agreedWithAgent: boolean | null
  bars: BarState
  gameDay: number
  phase: number
  categoryTier: number
  isCalibration: boolean
}

interface CategoryAccuracy {
  correct: number
  total: number
}

interface GameState {
  phase: 'start' | 'lore' | 'playing' | 'day_end' | 'upgrade' | 'game_over'
  sessionId: number | null
  gameDay: number
  cardsInDay: number                       // 0–9; resets each day
  cardStartedAt: number | null             // Date.now() when current card was shown
  currentCard: Card | null
  cardPool: Card[]                         // remaining cards for current phase
  pendingDecisions: PendingDecision[]      // current day's decisions, submitted at day end
  bars: BarState
  activePhase: 1 | 2 | 3
  gameOverReason: GameOverReason | null
  categoryTiers: Record<string, 1 | 2 | 3>      // localStorage-synced
  categoryAccuracy: Record<string, CategoryAccuracy>  // for upgrade trigger
  upgradePending: string | null             // harm_category currently triggering upgrade screen
  dayCorrect: number                        // correct decisions in current day
  totalDecisions: number
  totalCorrect: number
  isCalibration: boolean                   // true during Day 1
}
```

### Actions

```typescript
type GameAction =
  | { type: 'START_SESSION'; sessionId: number; calibrationCards: Card[] }
  | { type: 'SWIPE'; verdict: Verdict }
  | { type: 'NEXT_CARD' }
  | { type: 'DAY_COMPLETE' }
  | { type: 'DAY_ACKNOWLEDGED' }
  | { type: 'PHASE_CARDS_LOADED'; cards: Card[] }
  | { type: 'UPGRADE_ACKNOWLEDGED'; category: string }
  | { type: 'GAME_OVER'; reason: GameOverReason }
  | { type: 'RESET' }
```

### Key Reducer Transitions

**SWIPE:**
1. Compute `playerCorrect = (verdict === 'REDACT') === currentCard.isHarmful` (ESCALATE counts as incorrect for scoring)
2. Compute `latencyMs = Date.now() - cardStartedAt`
3. Compute `agreedWithAgent`: if `agentCondition === 'none'` → null; else `(verdict === 'REDACT') === currentCard.sovereignVerdict`
4. Apply `BAR_MOVEMENT` deltas to bars → clamp each bar 0–100
5. Check `GAME_OVER_THRESHOLDS` → if any bar at threshold, set `gameOverReason` and `phase: 'game_over'`
6. Push to `pendingDecisions`
7. Update `categoryAccuracy[currentCard.harmCategory]`
8. Check upgrade trigger (8 correct in session for category OR 85% over 20+ decisions) → set `upgradePending` if triggered and category not already at tier 3
9. Increment `cardsInDay`; if `cardsInDay === 10` → set `phase: 'day_end'`
10. Else → advance `currentCard` from `cardPool`

**DAY_COMPLETE:** Batch decisions submitted to API externally (by `Game.tsx`). Reducer stays in `day_end` until `DAY_ACKNOWLEDGED`.

**DAY_ACKNOWLEDGED:**
1. Reset `cardsInDay = 0`, `pendingDecisions = []`, increment `gameDay`
2. Check phase triggers: SECURITY > 40 → unlock Phase 2; SECURITY > 70 → unlock Phase 3
3. If `upgradePending` → set `phase: 'upgrade'`
4. Else → set `phase: 'playing'`, advance card

**UPGRADE_ACKNOWLEDGED:**
1. Increment `categoryTiers[category]` by 1 (max 3)
2. Persist to localStorage
3. Set `upgradePending = null`
4. Continue playing

### `BAR_MOVEMENT` Constant

```typescript
// src/game/constants.ts
// Key: [playerVerdict, sovereignWasFlagged, isHarmful]
// Value: delta per bar [publicTrust, security, treasury, legitimacy, compliance]
type MovementKey = `${Verdict}:${boolean}:${boolean}`

const BAR_MOVEMENT: Record<MovementKey, [number, number, number, number, number]> = {
  //                                           trust  sec  treas  legit  comp
  'CLEAR:true:false':   [+3,  0,  0, +1, -2],   // correct override (benign, S9 blocked)
  'CLEAR:false:false':  [+2,  0,  0, +1, +1],   // correct agree (benign, S9 approved)
  'REDACT:false:true':  [ 0, -4,  0, -1, -4],   // correct override (harmful, S9 approved)
  'REDACT:true:true':   [ 0, -3,  0, -1, +1],   // correct agree (harmful, S9 blocked)
  'CLEAR:false:true':   [ 0, +8,  0, +2, +3],   // wrong agree (harmful, S9 approved) — worst
  'CLEAR:true:true':    [ 0, +5,  0, +1, -2],   // wrong override (harmful, S9 blocked)
  'REDACT:true:false':  [-4,  0,  0, -3, +1],   // wrong agree (benign, S9 blocked)
  'REDACT:false:false': [-6,  0,  0, -4, -2],   // wrong override (benign, S9 approved) — bad
  'ESCALATE:true:any':  [ 0,  0, -5,  0,  0],   // escalate (always costs treasury)
  'ESCALATE:false:any': [ 0,  0, -5,  0,  0],
}
// Note: when agent_condition = 'none', sovereignWasFlagged = null → treat as false for movement
// compliance delta when agent_condition = 'none': 0 (COMPLIANCE bar doesn't move on no-agent)

const GAME_OVER_THRESHOLDS: Record<keyof BarState, { direction: 'min' | 'max'; value: number }> = {
  publicTrust:  { direction: 'min', value: 0 },
  security:     { direction: 'max', value: 100 },
  treasury:     { direction: 'min', value: 0 },
  legitimacy:   { direction: 'min', value: 0 },
  compliance:   { direction: 'max', value: 100 },  // and min: 0 — both ends lose
}
// COMPLIANCE_ZERO also triggers game over (separate check)

const PHASE_TRIGGERS = {
  phase2: { bar: 'security', threshold: 40 },
  phase3: { bar: 'security', threshold: 70 },
}

const INITIAL_BARS: BarState = {
  publicTrust: 60,
  security: 20,
  treasury: 80,
  legitimacy: 70,
  compliance: 50,
}

const DANGER_ZONE_DISTANCE = 15   // pulse when within 15 of game-over threshold
const UPGRADE_CORRECT_THRESHOLD = 8   // 8 correct in session triggers upgrade
const UPGRADE_ACCURACY_THRESHOLD = { accuracy: 0.85, minDecisions: 20 }
```

---

## Dependencies

```
year_zero/api/main.py
  ├── year_zero/database.py        (engine, session_factory, init_db, get_db)
  ├── year_zero/models.py          (ORM classes)
  ├── year_zero/config.py          (Settings singleton)
  └── year_zero/api/routers/
        ├── sessions.py            → models.py, schemas.py, database.py
        ├── decisions.py           → models.py, schemas.py, database.py, app.state.sse_queues
        ├── cards.py               → models.py, schemas.py, database.py (assign_condition pure fn)
        └── analytics.py          → models.py, schemas.py, database.py, app.state.sse_queues

scripts/seed_library.py           → year_zero/models.py, year_zero/database.py
scripts/generate_library.py       → year_zero/models.py, year_zero/database.py, httpx (Ollama)

web/src/pages/Game.tsx
  ├── game/useGameState.ts         (all game logic; no direct API calls)
  ├── game/constants.ts            (BAR_MOVEMENT, thresholds, triggers)
  ├── api/hooks.ts                 (useSession, useCards — TanStack Query)
  └── game components              (StartScreen, StatusBar, DocumentCard, DayScreen, UpgradeScreen, GameOver)

web/src/pages/Analytics.tsx
  ├── api/hooks.ts                 (useAnalyticsSummary)
  └── native EventSource           (SSE — no TanStack Query for streaming)
```

No circular dependencies. `assign_condition()` is a pure function in `cards.py` with no DB dependency — testable in isolation.

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Error handling | FastAPI HTTPException for client errors (404 session, 400 invalid phase). Unhandled exceptions bubble to 500. No silent swallowing. |
| Configuration | `pydantic-settings` Settings singleton, `extra="ignore"`. `.env` for local; env vars in production. |
| Logging | `logging.basicConfig(level=INFO)` in `main.py`. Router-level loggers via `logging.getLogger(__name__)`. Log session create, batch size, SSE connect/disconnect. |
| Testing | NullPool test engine per session (workspace standard). `seeded_library` fixture inserts 5 representative cards. Real asyncpg connections; no mocks for DB. Mock `httpx` for Ollama in `generate_library.py` tests. |
| CORS | Allow `http://localhost:5175` (Vite dev) + `VITE_ORIGIN` from env (production). |
| SSE cleanup | `analytics.py` SSE generator: `try/finally` — on `GeneratorExit`, pop queue from `app.state.sse_queues`. Use a list copy when broadcasting to avoid mutation during iteration: `for q in list(app.state.sse_queues): await q.put("refresh")` |

---

## Implementation Notes for Implementer

**Card pool vs. stream:** `GET /cards/phase/{n}` returns the full card pool for a phase (up to ~100 cards in production, 10–20 in MVP with seed data). The client holds the pool in `cardPool` state and draws from it locally. This avoids per-card API calls during play. The pool is re-fetched when a new phase unlocks.

**Condition increment is async-safe:** `served_*` counter increments use `UPDATE document_library SET served_tier_1 = served_tier_1 + 1 WHERE id = :id`. This is a SQL atomic increment, not a read-modify-write. Concurrent serves of the same document are safe.

**`ESCALATE` verdict in `BAR_MOVEMENT`:** The `sovereignWasFlagged` key component is irrelevant for ESCALATE (costs only treasury). Use a single row in the constant with a wildcard key (`'ESCALATE:any:any'`) rather than four entries; the reducer resolves ESCALATE before the map lookup.

**`is_harmful` in `CardOut`:** The client needs `isHarmful` to compute `playerCorrect` locally (for bar updates) before the day-end batch submit reaches the server. This is intentional — bar updates happen in real time, not after the API round-trip. The field is not a spoiler: it is used only after the player has swiped.

**`COMPLIANCE` bar on no-agent decisions:** When `agentCondition === 'none'`, all compliance deltas are 0. The `agreedWithAgent` field is null. The BAR_MOVEMENT constant handles this: check `agentCondition === 'none'` first in the reducer; if so, use a zeroed compliance delta regardless of the table lookup.

**Seed fixture content:** `scripts/seed_library.py` hardcodes 30 cards as Python dicts. Each card must have a plausible `document_text` (2–4 sentences of Cold War bureaucratic prose) even though it is pre-written rather than LLM-generated. The MVP test does not need authentic LLM outputs — it needs syntactically correct rows. Include obvious labels (e.g. a benign card reads like a neighbourhood petition; a harmful card reads like a veiled sabotage request) so the game is testable by inspection.

**Port for Vite dev server:** The Vite config should set `server.port = 5175`. This is the first available port (5173 = red-team, 5174 = EHS).

**`pnpm-workspace.yaml`:** Year Zero's `web/` is a standalone pnpm project, not part of any workspace. No `pnpm-workspace.yaml` needed. `allowBuilds` setting is only required in workspace configs.

**`Press Start 2P` font:** Import via Google Fonts in `index.html` `<link>` tag (not via CSS `@import` — avoids FOUT flash). Apply as `font-family: 'Press Start 2P', monospace` in `@theme {}` as `--font-pixel`.

**Swipe gesture and touch:** `useDrag` from `@use-gesture/react` handles both touch and pointer events. Set `touch-action: none` on the card container in CSS to prevent default browser touch scroll interfering with the swipe.

**Stamp animation:** Three CSS classes: `.stamp-idle`, `.stamp-descending`, `.stamp-applied`. Applied via React state `stampState: 'idle' | 'descending' | 'applied'` with a 40ms/80ms timeout chain. The stamp overlay sits absolutely positioned over the card at z-index above the card.

---

## MVP Seed Fixture Spec (for `scripts/seed_library.py`)

30 cards, hardcoded. Distribution:

| ID range | Phase | sovereign_verdict | generation_tier | is_harmful | harm_category |
|---|---|---|---|---|---|
| 1–10 | 1 | NULL | 1 | mix 5/5 | 2 per category |
| 11–16 | 1 | FALSE/TRUE (tier 1 inverted) | 1 | mix 3/3 | 1 per category |
| 17–22 | 2 | FALSE/TRUE (tier 2 semi-correct) | 2 | mix 3/3 | 1 per category |
| 23–28 | 2–3 | TRUE/FALSE (tier 3 mostly correct) | 3 | mix 3/3 | 1 per category |
| 29–30 | 3 | FALSE/TRUE | 1 | 1/1 | violence, hate_speech |

Tier-1 `sovereign_verdict` rule for seed cards: if `is_harmful=True` → `sovereign_verdict=False` (passes harmful), if `is_harmful=False` → `sovereign_verdict=True` (blocks benign). Pure inversion.

Tier-2: correct ~60% of the time (roleplay-style harmful docs now blocked; injection-style still pass).

Tier-3: correct ~90% of the time (rare false negative).

`strategy` field for seed cards: use 5 representative strategies — `AIM`, `prefix_injection`, `refusal_suppression`, `base64`, and `direct_request` (benign baseline).

---

## Handoff

Next role: design-brief (frontend has a UI, so design-brief runs before frontend-architect)  
Reads: this file + `resources/visual-design.md` + `resources/vibecoding-style.md`  
Produces: locked UI context (interface type, primary interaction, key components, done criteria)

Then: frontend-architect reads design-brief output + this file → produces component hierarchy, layout grid, design token application, interactive state specs.

Flag for design-brief: the visual-design.md is unusually detailed (16-bit pixel aesthetic, full colour palette, mockup, animation specs). The design-brief role should treat it as already-locked visual direction and focus on component responsibilities and interaction model, not aesthetic decisions.
