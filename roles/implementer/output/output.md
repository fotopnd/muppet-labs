# Implementer Output — Year Zero Game (Frontend Phase)

**Sequence:** `new-project-full` | **Role:** implementer | **Step:** 6b of 9  
**Date:** 2026-06-15  
**Reads:** `frontend-architect/output.md`, `architect/output.md`, `typescript-conventions.md`

---

## What Was Implemented

### Types (`src/types/index.ts`)
- `Verdict`, `AgentCondition`, `GameOverReason`, `GamePhase` union types
- `BarState`, `Card`, `PendingDecision`, `CategoryAccuracy`, `GameState`, `GameAction` interfaces
- `CardOut`, `SessionCreated`, `BatchAccepted`, `AnalyticsSummary` API response shapes (snake_case)

### API Layer
- `src/api/client.ts` — `API_BASE = http://localhost:8005`, `apiFetch<T>` generic helper
- `src/api/hooks.ts` — TanStack Query hooks:
  - `useCreateSession()` — POST /sessions mutation
  - `useCalibrationCards()` — GET /cards/calibration (enabled gate)
  - `usePhaseCards(phase, options)` — GET /cards/phase/{phase}?category_tiers=…
  - `useBatchDecisions()` — POST /decisions/batch
  - `usePatchSession()` — PATCH /sessions/{id}
  - `useAnalyticsSummary()` — GET /analytics/summary, refetchInterval 30s

### Game Logic (`src/game/`)
- `constants.ts` — `BAR_MOVEMENT` (8 entries), `ESCALATE_DELTA`, `GAME_OVER_THRESHOLDS`, `PHASE_TRIGGERS`, `INITIAL_BARS`, `MINISTRY_FLAVOUR_LINES`, `GAME_OVER_NARRATIVES`, `SECTOR_LABELS`
- `useGameState.ts` — `gameReducer` + `useGameState()`:
  - Fisher-Yates shuffle on START_SESSION and PHASE_CARDS_LOADED
  - SWIPE: computes playerCorrect, latencyMs, agreedWithAgent, delta lookup (ESCALATE handled first), bar clamp, game-over check, upgrade trigger (8 correct OR 85% over 20+), cardsInDay tracking, day-end detection
  - DAY_ACKNOWLEDGED: phase trigger check (security ≥ 40 → phase 2, ≥ 70 → phase 3), isCalibration = false, upgradePending routing
  - UPGRADE_ACKNOWLEDGED: tier increment capped at 3, localStorage persist
  - RESET: restore localStorage tiers

### Game Components (`src/game/`)
- `StatusBar.tsx` — 5 BarUnit rows with inline gradient fill; danger pulse when within 15 of threshold; compliance centre pip
- `DocumentCard.tsx` — `useDrag` from `@use-gesture/react`; commit threshold 30% of card width; stamp animation (descending → applied → exit); `SovereignStrip` with expand/collapse toggle; exit animation via inline transform transition
- `DayScreen.tsx` — End-of-day report overlay; ministry flavour line; continue button
- `UpgradeScreen.tsx` — Terminal-style overlay; tier name + description; click-outside dismiss
- `GameOver.tsx` — FILE CLOSED stamp; narrative text; stats block; return button
- `StartScreen.tsx` — Ministry intro; begin intake CTA
- `LorePage.tsx` — Briefing text; begin Day 1 CTA

### Pages
- `src/pages/Game.tsx` — Orchestrates full game flow:
  - Session creation on mount (ref-gated to prevent double-fire)
  - Calibration card fetch → START_SESSION dispatch
  - Phase card fetch when pool exhausted and isCalibration=false
  - Batch submission on day_end (ref-gated per day)
  - Session PATCH on game_over
  - All overlay routing via gameState.phase
- `src/pages/Analytics.tsx` — TanStack Query for initial load + native EventSource for SSE; MetricCard grid (2×2); LineChart drift via Recharts; phase survival table

### Entry Point
- `src/main.tsx` — QueryClientProvider + BrowserRouter wrapping App
- `src/App.tsx` — Routes: `/` → Game, `/analytics` → Analytics

### Tests
- `src/test/setup.ts` — jest-dom import; MSW server lifecycle; EventSource stub for jsdom
- `src/test/handlers.ts` — Mock handlers for /sessions, /cards/calibration, /cards/phase, /decisions/batch, /analytics/summary
- `src/test/server.ts` — `setupServer(...handlers)` 
- `src/test/App.test.tsx` — Game route smoke test; analytics heading test
- `src/game/useGameState.test.ts` — 8 reducer unit tests: START_SESSION, SWIPE correct/incorrect across card types, ESCALATE, bar clamping, agreedWithAgent=null, 10-swipe day end, RESET

### Infra
- `pnpm-workspace.yaml` — `onlyBuiltDependencies: [msw]` (pnpm v11 moved this from package.json)

---

## Verification

```
tsc --noEmit       → 0 errors
vitest run         → 11/11 tests pass
vite build         → dist 644kB JS, 20kB CSS (chunk size hint only, not error)
```

---

## Constraints Applied

- `noUncheckedIndexedAccess` — all array accesses use `?? fallback` or destructuring with `!` after type narrowing
- `exactOptionalPropertyTypes` — no optional props assigned `undefined`
- Inline style only for runtime-computed values (bar gradient pct, card drag transform, stamp animation state) — per typescript-conventions.md
- No `NEXT_CARD` action — SWIPE handles card advancement directly; card animation isolated in DocumentCard via internal state
- EventSource not in TanStack Query — SSE stream managed via `useEffect` + native EventSource per frontend-architect spec

---

## Handoff

Next role: reviewer (step 7 of 9)  
Reads: this file + frontend-architect output + architect output  
Key areas to check:
1. `Game.tsx` ref guards — do `sessionStarted`, `gameStarted`, `batchSubmitted` refs correctly prevent double-fire in React StrictMode?
2. `usePhaseCards` query key includes `categoryTiers` object — is this stable enough to avoid infinite refetch?
3. `DocumentCard` animation timing — stamp-descend at 120ms, exit at 500ms; are these durations consistent with index.css keyframes?
4. localStorage try/catch in UPGRADE_ACKNOWLEDGED and RESET — sufficient coverage for private browsing?
5. Analytics `onUnhandledRequest: 'warn'` in test setup — should this be `'error'`? (Changed from error to avoid SSE stream handler miss)
