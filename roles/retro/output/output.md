# Retro — Year Zero Game

**Sequence:** `new-project-full` | **Role:** retro | **Step:** 8 of 9  
**Date:** 2026-06-15

---

## Project

**Name:** year-zero-game  
**Sequence:** `new-project-full`  
**Sessions:** 3 (backend session; frontend session cut short by context limit; frontend completion + review + retro)  
**Roles that ran:** brief → planner → architect → design-brief → frontend-architect → implementer (6a backend) → implementer (6b frontend) → reviewer → retro  
**Step skipped:** `ui-reviewer` (step 7 in sequence) — went directly to reviewer

---

## What Went Well

**1. `BAR_MOVEMENT` constant spec in architect output**  
The architect specified the full 8-entry constant, key format (`${Verdict}:${boolean}:${boolean}`), ESCALATE handling rule ("resolve before map lookup"), and compliance-on-no-agent rule inline. The implementer dropped it in verbatim with zero ambiguity. This is the right level of detail for constants with non-obvious semantics — spec them completely in the architect, not vaguely.

**2. Two-phase implementer split (6a / 6b)**  
Backend green before frontend started. The implementer could build API hooks against a known, tested contract. No guessing at response shapes. The `backend-output.md` handoff file proved sufficient — no need to re-read the full architect output.

**3. `useReducer` for game state**  
Pure reducer, no API calls, no side effects. Directly unit-testable. Eight reducer tests written and passing. The architecture spec was right to push all logic into the reducer and all API orchestration into `Game.tsx`.

**4. MSW v2 setup was clean after the EventSource stub fix**  
One fix (add `MockEventSource` stub to `test/setup.ts`) and the full test suite ran. The pattern is: jsdom doesn't have EventSource; mock it globally in setup. Worth codifying.

**5. `staleTime: Infinity` on calibration and phase card queries**  
Cards are stable within a session — fetched once, never revalidated. The pattern was applied correctly and no redundant refetches were triggered. Correctly flagged by frontend-architect and correctly applied by implementer.

---

## What Could Have Gone Better

**1. `ui-reviewer` skipped**  
The `new-project-full` sequence requires `ui-reviewer` before `reviewer` for frontend projects. It was skipped in this session. The StartScreen button no-op (reviewer finding 3) — where "BEGIN INTAKE" dispatches a no-op RESET — would have been caught by a ui-reviewer as a broken interaction. The reviewer noted it as MINOR; a ui-reviewer would have flagged it as the intended primary interaction being broken.

**2. Calibration accuracy bug fell through two roles**  
The architect spec said "compute calibration stats at game over" but didn't note that `pendingDecisions` is ephemeral (cleared at `DAY_ACKNOWLEDGED`). The implementer wrote `state.pendingDecisions.filter(d => d.isCalibration)` which looks correct on a quick read. The reviewer caught it. The fix (add `calibDecisions`/`calibCorrect` fields to GameState) is 15 minutes but required three passes to discover.

Root cause: the architect spec described the output field (`calibration_accuracy`) but not where the data comes from mid-game. A single sentence in the architect — "calibration decisions must be accumulated in reducer state, not re-derived from pendingDecisions at game over" — would have prevented it.

**3. `apiFetch<void>` coordination gap between phases**  
The frontend implementer wrote `apiFetch<void>('/sessions/:id')` without verifying what the backend actually returns. The backend phase wrote the PATCH endpoint but the response format wasn't in `backend-output.md`. The test mock returns `HttpResponse.json(null, { status: 204 })` which silently covers the gap.

Root cause: `backend-output.md` listed the endpoint but not its response code or body. A "Response shapes" section in backend-output.md would have surfaced this.

**4. `pnpm-workspace.yaml` `onlyBuiltDependencies` confusion**  
pnpm v11 moved the `onlyBuiltDependencies` field from `package.json` to `pnpm-workspace.yaml`. The initial scaffold had it in the wrong place (plus a garbled `allowBuilds` entry from a previous session). One context window burned resolving this. Will happen again on every new TypeScript project using MSW.

**5. Context reconstruction overhead from prior session**  
The session started from a context summary + file re-reads. The summary was accurate but required re-reading `frontend-architect/output.md` and `architect/output.md` to resume. Total re-read overhead: ~40KB of context before the first file was written. A shorter, more targeted `backend-output.md` (which is what `implementer/output/backend-output.md` is supposed to be) would have reduced this.

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| 6b (frontend impl) | `architect/output.md` read in full (26KB); frontend implementer only needs the §Frontend reducer + §Constants + §Dependencies sections (~8KB) | medium | Architect should split output: `backend-spec.md` + `frontend-spec.md` for full-stack projects, OR add `## For Backend Implementer` / `## For Frontend Implementer` section headers |
| 6b (frontend impl) | `frontend-architect/output.md` read in full (14KB) including the full CSS token block that was already written to `index.css` | low | Frontend-architect should summarise token decisions as a one-line note ("tokens written to index.css — see file") not reproduce the entire CSS block |
| 7 (reviewer) | Full source files read (all 16 files, ~15KB combined) when most findings came from Game.tsx + hooks.ts + useGameState.ts (~6KB combined) | low | Reviewer should read the implementer's File Manifest first, then selectively read files flagged as complex or flagged in handoff notes |
| Session resume | Context summary + file re-reads added ~40KB overhead at session start | medium | `backend-output.md` should explicitly list the 3–4 files the frontend implementer needs to read, not just summarise what was built |

### Redundancy Patterns

- The CSS token block appears verbatim in `frontend-architect/output.md` AND in `src/index.css`. After 6b, reading frontend-architect just to get tokens is wasteful — the file is the ground truth.
- `architect/output.md` §Data Models (Python ORM) was loaded by the frontend implementer's session but is irrelevant to React component work.

### Scoping Recommendations

- `implementer (6b)` inputs table: replace `architect/output.md` with `implementer/output/backend-output.md` + `frontend-architect/output.md` — the architect output should be fully digested into these two files before 6b starts.
- `reviewer` process: add "read File Manifest first; only load files flagged in handoff notes or involving complex logic" to the role contract.

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `resources/routing.md` — `new-project-full` step 6a note | Add: "backend-output.md must include a 'Response Shapes' table: endpoint, method, response code, response body type. Frontend implementer reads this, not the full architect output." | Prevents apiFetch<void> class of coordination gaps | No |
| `resources/typescript-conventions.md` — Testing section | Add: "jsdom does not implement EventSource. Mock globally in test/setup.ts with a stub class. Do not install a polyfill." | Directly encountered this session; will recur | No |

### Skills to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `skills/setup-ts-pnpm.md` | Add a section: "pnpm v11 — onlyBuiltDependencies moved to pnpm-workspace.yaml. Remove from package.json; add `onlyBuiltDependencies: [msw]` (or relevant packages) to pnpm-workspace.yaml." | Will block every new project using MSW under pnpm v11 | No |

### Routing Changes

| Sequence | Change | Reason | Human decision required? |
|----------|--------|--------|--------------------------|
| `new-project-full` step 7 | Add a gate note: "ui-reviewer is REQUIRED for frontend projects, not optional. Do not proceed to reviewer without it." | Was skipped this session despite the spec saying "if project has frontend" | No |
| `new-project-full` step 6a note | Add: "backend-output.md is the primary handoff to 6b. It must be self-contained: list all endpoints, response shapes (code + body type), and any frontend-relevant constraints. The frontend implementer should not need to open architect/output.md." | Current spec doesn't mandate completeness of backend-output.md | No |

### New Resources or Skills Needed

**`skills/react-game-state.md`** — short (1 page) skill documenting the game-state-in-reducer pattern:
- `useReducer` with pure reducer + no API calls
- All API orchestration in parent component with `useEffect` + ref guards
- `key` prop on animated child components to reset animation state on card change
- EventSource in `useEffect` with `return () => es.close()`

Which roles would load it: `architect` (to choose the pattern), `implementer` (to apply it correctly). Would have prevented the calibration accuracy bug by making the "pendingDecisions is ephemeral" constraint explicit.

---

## One Change to Make Now

**`skills/setup-ts-pnpm.md`** — add pnpm v11 `onlyBuiltDependencies` note.

This is the single change that prevents the most immediate recurrence cost. Every new TypeScript project using MSW (or any package with build scripts) will hit this on first `pnpm exec`. The fix is two lines in `pnpm-workspace.yaml` plus removing the stale `pnpm` block from `package.json`, but discovering it costs a context window if undocumented.

---

## Handoff

Human reviews these findings and decides which recommendations to action.

Priority order for immediate actions:
1. `skills/setup-ts-pnpm.md` — pnpm v11 note (5 min, prevents next-session friction)
2. `resources/routing.md` — mandate `ui-reviewer` and add `backend-output.md` response shapes requirement (10 min)
3. `resources/typescript-conventions.md` — EventSource stub note (2 min)

Before production data collection (implementer pass):
- Finding 1 (calibration accuracy zero) — R1 from reviewer
- Finding 2 (apiFetch 204 guard) — R2 from reviewer
- Finding 9 (restore onUnhandledRequest: 'error') — 1 line

Before Hetzner deploy:
- R3: VITE_API_BASE env var
- Database migration: `uv run alembic upgrade head`
- Seed: `uv run seed-library`

Update `_config/project-state.md` to record that retro ran (2026-06-15) and which recommendations were actioned.
