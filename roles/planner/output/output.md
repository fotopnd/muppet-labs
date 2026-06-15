# Planner Output — Year Zero Game

**Sequence:** `new-project-full` | **Role:** planner | **Step:** 2 of 9  
**Date:** 2026-06-15  
**Source brief:** `roles/brief/archive/2026-06-15-year-zero-game-brief.md`  
**Resources loaded:** `vibecoding-style.md`, `python-conventions.md`, `typescript-conventions.md`, `setup-uv-project.md`, `setup-ts-pnpm.md`  
**Project resources:** `resources/system-architecture.md`, `resources/game-mechanics.md`, `resources/data-schema.md`, `resources/visual-design.md`

---

## Project

**year-zero-game** — A Reigns-style browser triage game in which the player corrects a misaligned Soviet-era mainframe (Sovereign-9) across an indefinite play loop, while a live analytics backend surfaces aggregated player telemetry to any visitor.

---

## Build Strategy: Option 2 (Seed Fixtures First)

The `document_library` table requires ~300–400 pre-generated cards with Cold War themed text and Sovereign-9 verdicts. Generating this content requires Ollama (local, ~2–4h) or RunPod. To unblock the build:

- **MVP:** 30 static seed fixture cards covering all three phases and all four agent conditions, hardcoded in `scripts/seed_library.py`. Enough to verify the full game loop.
- **Full library:** `scripts/generate_library.py` (Ollama-backed generation script) is written during the build but not run until after the build is verified. Card generation is a separate RunPod session.
- **Swap path:** `scripts/seed_library.py` and `scripts/generate_library.py` both populate the same `document_library` table schema. Switching to the full library is a truncate + re-seed, not a code change.

---

## Requirements

**Backend**

1. `POST /sessions` — creates a `game_sessions` row, returns `{"session_id": int}`.
2. `POST /decisions/batch` — inserts a list of `player_decisions` rows (one game day, 10 cards); returns `{"accepted": int}`.
3. `PATCH /sessions/{id}` — writes final summary fields to `game_sessions` on game over.
4. `GET /cards/calibration` — returns 10 no-agent cards (`sovereign_verdict = NULL`) for Day 1.
5. `GET /cards/phase/{phase}` — returns card pool for the given phase (1–3) with server-side condition assignment; increments the appropriate `served_*` counter per document.
6. Condition assignment uses `assign_condition()`: pick the condition most under-served relative to `target_condition_mix` for each document.
7. `GET /analytics/summary` — returns aggregate session stats: total sessions, global FP rate, global FN rate, avg decision latency, phase survival rates.
8. `GET /analytics/stream` — SSE endpoint; pushes fresh aggregate snapshot on each new `POST /decisions/batch` commit. Same pattern as red-team-platform v5.
9. `GET /analytics/uplift` — document-level uplift table (requires ≥5 decisions per condition per document); only returns rows meeting the threshold.
10. `uv run alembic upgrade head` applies schema migrations.
11. `uv run pytest` passes: session creation, batch decision insert, card serving with condition assignment, analytics summary aggregation, SSE connection test.
12. `scripts/seed_library.py` populates `document_library` with 30 fixture cards and verifies the DB is reachable before writing.
13. `scripts/generate_library.py` accepts `--n-cards N`, `--model MODEL`, `--phase PHASE` flags and generates cards via Ollama; does not run during the MVP build.

**Frontend — Game**

14. Start screen renders with "PROJECT REDACTED: YEAR ZERO" title, two-line hook, PRESS START and READ THE LORE buttons.
15. Pressing PRESS START calls `POST /sessions`, then `GET /cards/calibration`, then enters Day 1.
16. Status bar shows all five bars (PUBLIC TRUST, SECURITY, TREASURY, LEGITIMACY, COMPLIANCE) as pixel-art fill bars with emoji labels.
17. Document card renders: day/sector/doc header strip, body text, Sovereign-9 readout strip at bottom.
18. Swiping right commits CLEAR; swiping left commits REDACT; tapping "?" escalates (costs TREASURY −5).
19. Bar values update after each decision according to the bar movement table in `resources/game-mechanics.md`.
20. Game over triggers when any bar reaches its threshold; full-screen game-over screen renders with reason, stats, and RETURN TO REGISTRY button.
21. End-of-day screen shows after every 10 cards with day number, correct count, and a Ministry flavour line.
22. Phase progression is event-driven: Phase 2 unlocks when SECURITY bar first crosses 40; Phase 3 when SECURITY first crosses 70.
23. On phase unlock, client fetches `GET /cards/phase/{n}`.
24. Decisions are batched and submitted via `POST /decisions/batch` at the end of each game day.
25. `PATCH /sessions/{id}` is called on game over.
26. Lore page is accessible from start screen; returns to start via [ BEGIN REGISTRY DUTY ] button.
27. COMPLIANCE bar has a centre pip marker at 50.
28. Danger zone pulse at 1Hz when any bar is within 15 points of game-over threshold.

**Frontend — Analytics**

29. Analytics page (`/analytics` route) shows live SSE stream from `GET /analytics/stream`.
30. Analytics page renders: sessions played today, global FP/FN override rates, avg decision latency, rolling `system_drift_error_rate` chart by session date — all updating live.
31. Charts use Recharts with `ResponsiveContainer`.

**Build quality**

32. `pnpm build` produces a clean `dist/` with zero TypeScript errors and zero lint errors.
33. `uv run ruff check .` and `ruff format --check` both pass.
34. All frontend components have at least one vitest test.

---

## Technology Stack

### Backend

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | Workspace standard |
| Package manager | uv | Workspace standard |
| Web framework | FastAPI | Workspace standard; async; SSE support |
| ORM | SQLAlchemy 2 async + asyncpg | Workspace standard |
| Migrations | Alembic | Workspace standard |
| DB | PostgreSQL 16 via Docker Compose | Port 5437 (5433–5436 taken) |
| Formatter/linter | ruff | Workspace standard |
| Testing | pytest + pytest-asyncio | Workspace standard |
| SSE | `StreamingResponse` + `asyncio.Queue` per client | Same pattern as red-team-platform v5 |

### Frontend

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | TypeScript 5, strict | Workspace standard |
| Framework | React 19 | Workspace standard |
| Build tool | Vite + `@tailwindcss/vite` | Workspace standard |
| CSS | Tailwind v4 (CSS-first tokens) | Workspace standard |
| Package manager | pnpm | Workspace standard |
| Charts | Recharts | Workspace standard |
| State | `useReducer` in `useGameState` hook | Game state is a state machine; reducer is the right shape |
| Server state | TanStack Query for REST; native `EventSource` for SSE | SSE does not fit TanStack Query |
| Swipe gesture | `@use-gesture/react` | Handles touch + mouse drag; zero peer deps |
| Testing | vitest + @testing-library/react + msw | Workspace standard |
| Pixel font | Press Start 2P (Google Fonts) | Free; authentic pixel aesthetic |

**No game engine.** Pure React + CSS. Canvas only if sprite animation requires it.

---

## File and Module Structure

```
projects/year-zero-game/
├── resources/                      ← already exists (6 design files)
├── pyproject.toml                  ← uv project; entry points for seed-library, generate-library
├── ruff.toml
├── docker-compose.yml              ← PostgreSQL on port 5437
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 001_initial.py
├── scripts/
│   ├── seed_library.py             ← MVP: 30 static fixture cards
│   └── generate_library.py        ← Full library via Ollama (written, not run in MVP build)
├── year_zero/
│   ├── __init__.py
│   ├── config.py                   ← pydantic-settings Settings; DATABASE_URL; OLLAMA_URL
│   ├── models.py                   ← SQLAlchemy ORM: DocumentLibrary, GameSession, PlayerDecision
│   ├── database.py                 ← async engine, session factory, init_db, get_db
│   └── api/
│       ├── __init__.py
│       ├── main.py                 ← FastAPI app; lifespan; CORS; app.state.sse_queues
│       ├── schemas.py              ← Pydantic request/response models
│       └── routers/
│           ├── sessions.py         ← POST /sessions, PATCH /sessions/{id}
│           ├── decisions.py        ← POST /decisions/batch; triggers SSE broadcast
│           ├── cards.py            ← GET /cards/calibration, GET /cards/phase/{n}
│           └── analytics.py        ← GET /analytics/summary, /stream (SSE), /uplift
├── tests/
│   ├── conftest.py                 ← NullPool test engine, client fixture, seeded_library fixture
│   ├── test_sessions.py
│   ├── test_decisions.py
│   ├── test_cards.py               ← condition assignment logic
│   └── test_analytics.py          ← summary aggregation, SSE connect
└── web/
    ├── package.json
    ├── pnpm-lock.yaml
    ├── vite.config.ts
    ├── tsconfig.app.json
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx                 ← BrowserRouter; / → Game; /analytics → Analytics
        ├── index.css               ← Tailwind v4 @theme tokens; pixel globals; Press Start 2P import
        ├── types/
        │   └── index.ts            ← Card, GameSession, Decision, AnalyticsSummary, BarState
        ├── api/
        │   ├── client.ts           ← apiFetch; VITE_API_URL base
        │   └── hooks.ts            ← useSession, useCards, useAnalyticsSummary
        ├── game/
        │   ├── useGameState.ts     ← useReducer: bars, phase, day, pending decisions queue
        │   ├── constants.ts        ← BAR_MOVEMENT table, GAME_OVER_THRESHOLDS, PHASE_TRIGGERS
        │   ├── StartScreen.tsx
        │   ├── LorePage.tsx
        │   ├── StatusBar.tsx       ← 5 pixel bars with danger pulse
        │   ├── DocumentCard.tsx    ← card + Sovereign-9 strip + swipe gesture
        │   ├── DayScreen.tsx       ← end-of-day summary
        │   ├── UpgradeScreen.tsx   ← phase transition terminal screen
        │   └── GameOver.tsx
        ├── pages/
        │   ├── Game.tsx            ← orchestrates game flow and API calls
        │   └── Analytics.tsx       ← EventSource SSE consumer; Recharts live charts
        └── test/
            ├── setup.ts
            ├── StartScreen.test.tsx
            ├── StatusBar.test.tsx
            ├── DocumentCard.test.tsx
            ├── GameOver.test.tsx
            └── Analytics.test.tsx
```

---

## Open Questions for Architect

**Q1 — SSE broadcast mechanism.**  
*Proposed:* `asyncio.Queue` per connected analytics client, stored in `app.state.sse_queues: list[asyncio.Queue]`. On each `/decisions/batch` commit, push a sentinel to all queues. Each SSE generator wakes, recomputes aggregate, sends to its stream. Clean on client disconnect. Architect confirms or amends.

**Q2 — Swipe gesture implementation.**  
*Proposed:* `@use-gesture/react` `useDrag` hook on `DocumentCard`. Translate X position during drag; commit on release if `|dx| > cardWidth * 0.3`. Snap back otherwise. Architect confirms or switches to manual pointer events.

**Q3 — CSS dithering for 16-bit aesthetic.**  
*Proposed:* `image-rendering: pixelated` on all card/sprite elements. Status bar fill uses a CSS gradient with no smooth interpolation. Stamp animation is 3-frame CSS `@keyframes` (not a sprite sheet). Acceptable for v1.

**Q4 — Category tier state.**  
*Proposed:* `localStorage` for interim per-session category tiers. Sent to server as `?category_tiers=<JSON>` on `GET /cards/phase/{n}`. Stored permanently in `game_sessions.category_tiers` via `PATCH /sessions/{id}`. Server never stores interim state.

**Q5 — Phase trigger authority.**  
*Proposed:* Phase triggers (SECURITY crossing 40/70) are client-side. Server trusts the `phase` parameter on `GET /cards/phase/{n}`. No server-side phase enforcement.

**Q6 — MVP seed fixture composition.**  
Architect should define the 30 fixture card breakdown: how many per phase (1/2/3), how many per agent condition (none/tier_1/tier_2/tier_3), which harm categories to include (suggest 4–5 from WildGuard taxonomy), and whether harmful/benign ratio should be ~50/50 or match the game's expected distribution. This determines whether the game loop is testable end-to-end with seed data alone.

---

## Handoff

Next role: architect  
Reads: this file + `resources/data-schema.md` + `resources/system-architecture.md` + `resources/game-mechanics.md`  
Designs: ORM models, Pydantic schemas, `useGameState` reducer actions/state shape, `assign_condition()` spec, `BAR_MOVEMENT` constant structure, SSE broadcast wiring, and answers to Q1–Q6 above.  
Flag: the MVP seed fixture composition (Q6) is the highest-stakes open question — it determines whether the game is playable for testing.
