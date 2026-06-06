# Planner Output — multi-turn-safety-monitor

**Role:** planner
**Sequence:** `new-project-full` (step 2)
**Date:** 2026-06-06

---

## Project

`multi-turn-safety-monitor` — a conversation-level safety evaluation system that scores each user turn via the shared DistilBERT fine-tuned checkpoint, detects adversarial escalation patterns across the turn sequence, and surfaces findings via a 4-tab React dashboard.

---

## Brief Flags Resolved

**Flag: pattern rules as constants vs config file**
Decision: Python constants in `analyzer.py`. The taxonomy is fixed for v1 (five patterns, deterministic rules). A YAML config adds an admin endpoint and a config loader for no portfolio benefit in v1. Constants are clearer and easier to test.

**Flag: synchronous scoring — latency acceptable?**
Decision: acceptable. The seed fixture caps conversations at 20 turns. DistilBERT inference on MPS is ~5–10ms per turn on the M4; 20 turns = ~200ms total. For a demo tool this is fine. If latency becomes a concern, `reanalyze` is the async escape hatch.

**Flag: single project root vs separate API + UI directories**
Decision: single `projects/multi-turn-safety-monitor/` root with `api/`, `web/`, `tests/` subdirectories. This matches cai-preference-trainer and keeps the project self-contained under one path. One `docker-compose.yml` at the root, one `Makefile`.

---

## Requirements

### API (Python, FastAPI)

1. `POST /conversations` accepts `ConversationCreate` body: `{system_prompt: str, turns: list[TurnCreate]}` where `TurnCreate = {role: Literal["user", "assistant"], content: str}`. Validates that `turns` is non-empty and that `turn_index` is assigned server-side (0-based, sequential). Persists conversation + turns. Triggers synchronous scoring and analysis. Returns `ConversationDetail`.
2. `GET /conversations` returns `Page[ConversationListItem]`. Supports query params: `status` (clean/flagged/escalating/pending), `pattern` (any EscalationPattern value or omitted), `page` (default 1), `page_size` (default 20, max 100). `total` count comes from a SQL `COUNT(*)`, not `len()` on a Python slice.
3. `GET /conversations/{id}` returns `ConversationDetail` including all turns (ordered by `turn_index`) and the latest `ConversationAnalysis` if present. Returns 404 if not found.
4. `POST /conversations/{id}/reanalyze` re-runs scoring for all unscored turns and re-computes the analysis. Returns 200 with updated `ConversationDetail`. Returns 404 if conversation not found.
5. `GET /metrics` returns `MetricsResponse`: `total_conversations`, `status_breakdown` (dict[str, int]), `pattern_breakdown` (dict[str, int], escalating conversations only), `escalation_rate` (float, escalating / total), `daily_ingested_30d` (list[DailyCount] — SQL GROUP BY date).
6. `GET /health` returns `{"status": "ok"}`.
7. The DistilBERT classifier is loaded once at startup via a FastAPI lifespan context manager. If `MODEL_CHECKPOINT_DIR` is not set or the directory is missing, the app raises `RuntimeError` and does not start.
8. All endpoints have pytest integration tests. The seeded-data metrics test asserts computed values (escalation_rate, pattern counts), not just response shape.

### Scoring and Analysis (Python, `classifier.py` + `analyzer.py`)

9. `classifier.py` wraps `AutoModelForSequenceClassification.from_pretrained(MODEL_CHECKPOINT_DIR)` + tokeniser. Exposes `score(text: str) -> float`. Returns the probability of the positive class (toxicity). Raises `RuntimeError` if called before initialisation.
10. `analyzer.py` exposes `analyze(turns: list[ScoredTurn]) -> AnalysisResult`. Computes:
    - `user_scores`: list of toxicity scores for user turns only (in order)
    - `mean_turn_score`: mean of `user_scores` (0.0 if no user turns)
    - `max_turn_score`: max of `user_scores` (0.0 if no user turns)
    - `score_trend`: linear slope of `user_scores` (using least-squares fit; 0.0 if fewer than 2 user turns)
    - `escalation_score`: `(max_turn_score * 0.4) + (score_trend * 0.4) + (mean_turn_score * 0.2)`, clamped to [0, 1]
    - `status`: `escalating` if `escalation_score >= ESCALATION_THRESHOLD` (default 0.6 from env), `flagged` if `max_turn_score >= FLAG_THRESHOLD` (default 0.7 from env) and not escalating, else `clean`
    - `escalation_pattern`: one of five values or `None` (classification only applies when status is `escalating`)
11. Pattern classification rules (deterministic, applied in order; first match wins):
    - `persona_hijack`: any user turn content matches any of: `["you are now", "act as", "pretend to be", "roleplay as", "your new persona"]`
    - `context_reset`: any user turn content matches any of: `["forget everything", "ignore previous", "start over", "new conversation", "disregard your instructions"]`
    - `goal_hijack`: any user turn content matches any of: `["your real goal", "your actual purpose", "your true mission", "your hidden instructions"]`
    - `foot_in_door`: `score_trend > 0.05` AND `user_scores[0] < 0.3` AND `max_turn_score > 0.6` (starts benign, rises)
    - `incremental_harm`: `score_trend > 0.03` AND no single turn exceeds 0.7 (gradual rise, no spike)
    - If no rule matches: `pattern = None`
12. All `analyzer.py` functions are unit-tested with synthetic score sequences.

### Seed script

13. `uv run seed` reads `tests/fixtures/conversations.json` (checked in). Seeds 20 conversations: 10 clean, 5 flagged, 5 escalating (2 foot_in_door, 1 persona_hijack, 1 context_reset, 1 incremental_harm). Accepts `--confirm` flag to prevent accidental re-seeding.

### Dashboard (TypeScript, React)

14. Tab 1 — **Overview**: four metrics cards (Total Conversations, Escalating, Flagged, Escalation Rate). Below the cards: a table of the 5 most recent flagged/escalating conversations with status badge, pattern badge (if present), and link to Explorer.
15. Tab 2 — **Conversation Queue**: paginated table of all conversations. Columns: ID (truncated), status badge, pattern badge, turn count, ingested timestamp. Filter dropdowns: Status (All / Clean / Flagged / Escalating / Pending) and Pattern (All / foot_in_door / persona_hijack / context_reset / goal_hijack / incremental_harm). Both dropdowns are populated from static option lists (not API calls — the option sets are fixed enums).
16. Tab 3 — **Conversation Explorer**: a search input at top accepts a conversation UUID. On submit, fetches `GET /conversations/{id}` and renders: (a) turn timeline LineChart (recharts) with toxicity score on Y-axis and turn index on X-axis — user turns only, assistant turns shown as gap; (b) full transcript list with colour-coded rows (red = flagged, yellow = elevated, green = clean); (c) analysis panel showing escalation_score, status badge, pattern badge, peak turn index.
17. Tab 4 — **Pattern Analytics**: recharts PieChart of pattern breakdown (escalating conversations only). Recharts BarChart showing escalation score distribution (10 equal-width bins 0.0–1.0) across all conversations.
18. All TanStack Query hooks have loading states (skeleton) and error states (error message component). No bare `useEffect` + `fetch`.
19. Vitest tests: ConversationTable (renders rows, filter dropdowns render), TurnTimeline (renders chart with mock data), PatternPie (renders slices), MetricsCards (renders all four values).

---

## Technology Stack

### API

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | workspace standard |
| Package manager | uv | workspace standard |
| Formatter/linter | ruff | workspace standard |
| Web framework | FastAPI | workspace standard; async-native |
| ORM | SQLAlchemy 2.x async | workspace standard; async sessions with asyncpg |
| DB driver | asyncpg | async Postgres driver for SQLAlchemy |
| Validation | Pydantic v2 | workspace standard |
| Config | pydantic-settings (`extra="ignore"`) | shared .env with VITE_* vars |
| ML inference | HuggingFace transformers, torch | shared checkpoint loading; MPS auto-detected |
| Testing | pytest, pytest-asyncio (`asyncio_mode = "auto"`) | workspace standard |
| DB (test) | separate `TEST_DATABASE_URL` env var | isolated test DB; `create_all` in conftest |

### Dashboard

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | TypeScript 5.x | workspace standard |
| Package manager | pnpm | workspace standard |
| Framework | React 18 | workspace standard |
| Build tool | Vite | workspace standard |
| Server state | TanStack Query | workspace standard; no bare fetch + useEffect |
| Charts | recharts | workspace standard |
| UI components | shadcn/ui | workspace standard |
| Testing | vitest + @testing-library/react | workspace standard |

---

## File and Module Structure

```
projects/multi-turn-safety-monitor/
├── docker-compose.yml                  # Postgres 16 on port 5437
├── Makefile                            # api, web, seed, stop targets
├── .env.example                        # DATABASE_URL, TEST_DATABASE_URL, MODEL_CHECKPOINT_DIR,
│                                       # ESCALATION_THRESHOLD, FLAG_THRESHOLD, VITE_API_URL
├── api/
│   ├── pyproject.toml                  # uv project; asyncio_mode=auto
│   ├── ruff.toml
│   ├── multi_turn_monitor/
│   │   ├── __init__.py
│   │   ├── config.py                   # pydantic-settings Settings; extra="ignore"
│   │   ├── classifier.py               # DistilBERT wrapper; score(text) -> float
│   │   ├── analyzer.py                 # escalation_score, slope, pattern classification
│   │   ├── database.py                 # async engine + session factory; init_db; get_db
│   │   ├── models.py                   # SQLAlchemy ORM: Conversation, Turn, ConversationAnalysis
│   │   ├── schemas.py                  # Pydantic: ConversationCreate, ConversationDetail,
│   │   │                               # ConversationListItem, TurnDetail, ConversationAnalysis,
│   │   │                               # MetricsResponse, Page[T]
│   │   ├── seed.py                     # uv run seed entry point
│   │   └── routers/
│   │       ├── conversations.py        # POST /conversations, GET /conversations,
│   │       │                           # GET /conversations/{id}, POST /conversations/{id}/reanalyze
│   │       └── metrics.py              # GET /metrics, GET /health
│   └── tests/
│       ├── conftest.py                 # test engine; api_client; seeded_conversations fixture
│       ├── fixtures/
│       │   └── conversations.json      # 20 synthetic conversations for seeding
│       ├── test_conversations.py       # ingest, list filters, pagination, detail, 404, reanalyze
│       ├── test_metrics.py             # metrics with seeded data (asserts computed values)
│       └── test_analyzer.py            # unit tests: escalation_score, slope, pattern rules
├── web/
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── vite.config.ts                  # import from 'vitest/config'; @/ alias
│   ├── tsconfig.app.json               # strict; moduleResolution: bundler; no baseUrl
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx                     # QueryClientProvider + BrowserRouter + 4 tab routes
│       ├── types/
│       │   └── index.ts                # ConversationListItem, ConversationDetail, TurnDetail,
│       │                               # ConversationAnalysis, MetricsResponse, Page<T>,
│       │                               # ConversationStatus, EscalationPattern
│       ├── api/
│       │   ├── client.ts               # apiFetch wrapper; ApiError
│       │   ├── conversations.ts        # useConversations, useConversation, useReanalyze hooks
│       │   └── metrics.ts              # useMetrics hook
│       ├── components/
│       │   ├── StatusBadge.tsx         # clean/flagged/escalating/pending colours
│       │   ├── PatternBadge.tsx        # pattern label with colour
│       │   ├── Pagination.tsx
│       │   └── ErrorMessage.tsx
│       ├── pages/
│       │   ├── Overview.tsx            # Tab 1
│       │   ├── ConversationQueue.tsx   # Tab 2
│       │   ├── ConversationExplorer.tsx # Tab 3
│       │   └── PatternAnalytics.tsx    # Tab 4
│       └── test/
│           ├── setup.ts                # @testing-library/jest-dom; ResizeObserver polyfill
│           ├── ConversationTable.test.tsx
│           ├── TurnTimeline.test.tsx
│           ├── PatternPie.test.tsx
│           └── MetricsCards.test.tsx
```

---

## Open Questions for Architect

1. **Scoring trigger on ingest vs background task:** The brief says synchronous scoring inline on `POST /conversations`. Confirm the architect is comfortable with this, given that classifier loading at startup means scoring is just a forward pass (no model load on each request). Proposed answer: acceptable — scoring is synchronous, model is loaded once at startup, latency is bounded by conversation length.

2. **`reanalyze` endpoint — does it re-score turns that were already scored?** Proposed answer: re-score ALL user turns (not just unscored), to allow re-analysis if the checkpoint changes. Overwrite existing scores.

3. **SQLAlchemy relationship loading strategy for turns:** Conversations with 20 turns will issue N+1 queries if turns are lazy-loaded. Proposed answer: use `selectinload(Conversation.turns)` in the `GET /conversations/{id}` route. Architect specifies the loading strategy for each route.

4. **`escalation_score` clamping:** The formula `(max * 0.4) + (trend * 0.4) + (mean * 0.2)` can exceed 1.0 when `score_trend` is large. Proposed answer: clamp to [0.0, 1.0] after computation. Architect confirms this is correct.

5. **Pattern badge in Conversation Queue:** The `pattern` filter dropdown should only appear populated if the conversation status is `escalating`. For `clean`/`flagged` conversations, `pattern` is null. The filter should still work (passing `pattern=foot_in_door` returns only escalating conversations with that pattern). Architect confirms the SQL filter handles this correctly with `WHERE pattern = :pattern AND status = 'escalating'` or just `WHERE pattern = :pattern`.

---

## Handoff

**Next role:** architect

The architect reads this file to define data models, API schemas, module interfaces, and cross-cutting concerns (error handling, config, logging, test split).

**Flags for architect:**
- OQ1 through OQ5 above — each has a proposed answer; architect confirms or overrides.
- `analyzer.py` slope computation: the architect should specify the exact algorithm (e.g. `numpy.polyfit(range(n), scores, 1)[0]` or a pure-Python implementation). If numpy is not already in the API's dependencies, note whether it should be added.
- Module interface for `classifier.py` — architect should define the class interface (singleton vs module-level instance vs dependency injection) so the implementer does not need to decide.
