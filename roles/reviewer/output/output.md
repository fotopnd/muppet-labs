# Reviewer Output — Year Zero Game

**Sequence:** `new-project-full` | **Role:** reviewer | **Step:** 7 of 9  
**Date:** 2026-06-15  
**Reads:** `implementer/output/output.md`, `typescript-conventions.md`, all source files

---

## Summary

Build is clean: 0 TypeScript errors, 11/11 tests pass, `vite build` succeeds. The game logic (reducer transitions, bar movement, upgrade trigger, game-over detection) is correct and well-structured. Two data-quality findings worth addressing before production: calibration accuracy is always 0 in the session record (finding 1), and `apiFetch<void>` will throw on a true 204 No Content response (finding 2). No blocking correctness issues.

---

## Correctness

**1. Calibration accuracy always 0 in `PATCH /sessions` — WARNING**  
`Game.tsx:83–86` — `patchSession` computes `calibDecisions` by filtering `state.pendingDecisions` for `isCalibration`. But `pendingDecisions` holds only the current day's decisions; it's cleared in `DAY_ACKNOWLEDGED` (`pendingDecisions: []`). Game over always fires during a SWIPE mid-day (never from `day_end`). So by the time game over happens (anytime after Day 1), the calibration decisions have been batch-submitted and cleared. Result: `calibration_decisions: 0, calibration_accuracy: 0` in every session record except games that end on Day 1.

Fix: add `calibDecisions: number` and `calibCorrect: number` to `GameState`, increment both in the SWIPE case when `state.isCalibration === true`. Reference these in the `patchSession` call instead of filtering `pendingDecisions`.

**2. `apiFetch<void>` unconditionally calls `res.json()` — WARNING**  
`api/client.ts:9` — if `PATCH /sessions/{id}` returns HTTP 204 with no response body, `res.json()` throws `SyntaxError: Unexpected end of JSON input`. The test mock returns `HttpResponse.json(null, { status: 204 })` which has a `"null"` body, so tests pass. Real FastAPI behaviour depends on the router implementation (not reviewed in this pass).

Fix: `if (res.status === 204) return undefined as T` before calling `res.json()`.

**3. `StartScreen` "Begin Intake" button dispatches a no-op — MINOR**  
`Game.tsx:143` — `onStart={() => dispatch({ type: 'RESET' })}`. When `phase === 'start'`, RESET returns to `'start'` — no change. The game advances automatically via the `gameStarted` effect once `sessionId` + `calibCards` resolve. The StartScreen functions as a loading screen and the button does nothing. The UX reads as "press to start" but start is automatic.

**4. `handleReturn` setTimeout can leak after unmount — MINOR**  
`Game.tsx:127–130` — `setTimeout(() => { sessionStarted.current = false; createSession.mutate(undefined) }, 50)` is not cancelled on unmount. If the user navigates to `/analytics` within 50ms of pressing Return, the timer fires on a detached closure. TanStack Query handles stale mutations gracefully (no crash), but the ref mutation and `mutate` call are technically side-effects on an unmounted component.

---

## Style

**5. `interface` for shape types — MINOR**  
`types/index.ts` — `BarState`, `Card`, `PendingDecision`, `CategoryAccuracy`, `GameState` are declared as `interface`. Convention: use `type` for shapes and unions; `interface` only when declaration merging is intentional. None of these are extended or merged.

**6. Relative imports instead of `@/` alias — MINOR**  
All cross-directory imports use relative paths (`'../types'`, `'../game/constants'`). Convention calls for `@/` path alias. One-level-up traversals are technically permitted by the "no `../../` climbing" rule, but the spirit is `@/` throughout.

**7. `SECTOR_LABELS` is a dead export — MINOR**  
`game/constants.ts` — defined but never imported by any component. Remove or use it.

---

## Tests

**8. Upgrade trigger path untested**  
Neither `upgradePending` being set after 8 correct in a category, nor the `UPGRADE_ACKNOWLEDGED` reducer transition, nor `UpgradeScreen` rendering, are tested. The upgrade path gates tier progression which affects `categoryTiers` in the session record.

**9. `onUnhandledRequest: 'warn'` weakens coverage**  
`test/setup.ts` — changed from `'error'` to `'warn'`. Since `MockEventSource` is a stub that never makes real network requests, there's no actual unhandled `/analytics/stream` request. Safe to restore `'error'` — the current setting would silently swallow any real missing mock handlers.

**10. Non-null assertion in test — MINOR**  
`game/useGameState.test.ts:42` — `dec!.playerCorrect`. Convention says avoid `!`; narrow with `expect(dec).toBeDefined()` first.

---

## Refactor Candidates

**R1. Calibration stats in reducer state**  
Add `calibDecisions: number` and `calibCorrect: number` to `GameState` (starts 0, increments in SWIPE when `isCalibration`). Fixes finding 1 and removes the brittle `pendingDecisions.filter(isCalibration)` in `Game.tsx`.

**R2. `apiFetch` 204 guard**  
One-line: `if (res.status === 204) return undefined as T` in `client.ts`. Required before the real backend is exercised.

**R3. `API_BASE` as env var**  
`api/client.ts:1` — hardcoded `http://localhost:8005`. Before Hetzner: `import.meta.env.VITE_API_BASE ?? 'http://localhost:8005'` + `.env.example` entry per conventions.

**R4. `handleReturn` session re-init**  
Replace `setTimeout(50)` with a state-driven flag: `needsNewSession: boolean` in `GameState` (set by RESET, cleared by START_SESSION). The `sessionStarted` effect watches this flag. Eliminates the race window.

**R5. `StartScreen` button intent**  
Gate the `gameStarted` effect on a `userReadyToStart: boolean` ref (set by the button click), or rename the button to "Loading…" if auto-advance is intentional.

---

## Verdict

**PASS WITH NOTES**

No blocking issues. The calibration accuracy bug (finding 1) corrupts session telemetry but doesn't affect gameplay. Recommend fixing R1 and R2 in an implementer pass before the first real data collection. R3 is required before Hetzner deploy.

---

## Handoff

Next role: retro (step 8 of 9)  
Reads: this file + all implementer outputs + planner output  
Produces: session retrospective — what worked, what didn't, what to carry forward to the deploy pass.

Items for next implementer pass before production data collection:
- R1: calibration accuracy zero (15 min)
- R2: apiFetch 204 guard (2 min)
- Finding 9: restore `onUnhandledRequest: 'error'` (1 line)
- R3: VITE_API_BASE env var (5 min, required for Hetzner deploy)
