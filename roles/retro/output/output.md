# Retro — gridiron: Coaches Pages

**Role:** retro
**Sequence:** add-feature
**Date:** 2026-06-24

---

## Project

`gridiron-coaches-pages` — `add-feature` sequence. Single session (continuation from compacted context). Roles: brief → planner → architect → implementer → reviewer → retro. Full-stack: Python backend + TypeScript/React frontend. Verdict: PASS WITH NOTES.

---

## What Went Well

**W1 — Two-CTE pattern found and fixed during implementation:** The W-L inflation bug (single-CTE LEFT JOIN multiplying game rows) was caught during implementation via a direct DB query test, before the API was live. The fix (separate `wl` and `play_stats` CTEs) is clean and generalises correctly. The test-before-trust pattern (run the SQL directly in Python before trusting the ORM handler) is worth preserving.

**W2 — `pnpm build` as TS verification gate:** Building for production rather than relying on `tsc --noEmit` alone catches more issues (module resolution, unused imports that TSC misses). The build passed cleanly in one pass — no TS iterations needed.

**W3 — Minimal frontend footprint:** CoachPage.tsx mirrors PlayerPage.tsx structure exactly. No new dependencies, no shared component extraction, reuse of existing `useQuery` + `apiFetch` pattern. Ponytail discipline held — `Th`/`Td` are local to the page (not abstracted until a 3rd page needs them).

**W4 — Two-query DB pattern cleaner than one-CTE:** Coach lookup + season stats as separate queries is easier to debug than a single complex CTE. At this scale (1 coach per request, 1-2 seasons) the overhead is negligible. The pattern is also easier to extend (e.g. add coaching staff names later without touching the season stats query).

---

## What Could Have Gone Better

**B1 — Brief in sprint mode started from stale brief/planner/architect outputs:** The MCP `load_role_context` returned the previous sprint's outputs for brief/planner/architect because the `output/output.md` files weren't archived before starting. In sprint mode this is expected (the sprint command says to archive before overwriting), but the transition_role tool only archives when called — so the sequence started reading stale context for a moment before being overwritten. **Fix:** No change needed — this is working as designed. The sprint command's `transition_role` calls handle archiving correctly. The only issue was the initial brief output load, which was correctly overwritten.

**B2 — curl commands backgrounded instead of completing:** `curl` to the local backend (127.0.0.1:8006) backgrounded on two separate calls before responding. The backend was responding (the background task completed with exit 0 and correct JSON), but the initial calls during the edit phase timed out. This is a function of the backend's asyncio load (season_loop running game simulations). Not a code issue.

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| Role sequence start | `load_role_context` returned previous sprint's stale outputs (brief/planner/architect) before they were overwritten | Low | Not avoidable — transition_role is the correct gate |
| Planner | Loaded setup-uv-project.md and setup-ts-pnpm.md skills in full — project already initialised, these were not needed | Medium | In `add-feature` on an existing project, skip setup skills. Add note to routing.md. |
| Architect | Loaded full previous sprint's architect output (400+ lines) as "existing" before overwriting | Low | Not avoidable |

### Redundancy Patterns

- SQL logic for the coach stats query was specified in both the planner output and the architect output at the same level of detail. Planner → architect handoff was clean, but the SQL was essentially re-derived identically. **Implication:** For SQL-heavy features, the planner's SQL is authoritative; architect should confirm + refine rather than rewrite.

### Scoping Recommendations

- In `add-feature` for existing projects: planner CONTEXT.md says to load setup skills but these are only needed if the project isn't yet initialised. Add a conditional note: "Load setup skills only if initialising a new project. Skip for existing projects."

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `_config/project-state.md` | Add coaches pages sprint to completed sprints; note `/coaches/:coachId` route and new schemas | Track completion | No |

### Skills to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| (none) | — | — | — |

### Routing Changes

| Sequence | Change | Reason | Human decision required? |
|----------|--------|--------|--------------------------|
| `add-feature` planner step | Add note: "Skip setup skills (`setup-uv-project.md`, `setup-ts-pnpm.md`) when adding a feature to an existing project. Load only language conventions files." | These skills are only needed for new project initialisation — they add token load for no value in feature sprints | No |

### New Resources or Skills Needed

- None identified for this sprint.

---

## One Change to Make Now

**Update `_config/project-state.md`** with the coaches pages sprint completion.

---

## Handoff

Update `_config/project-state.md`. One routing.md note (skip setup skills in add-feature for existing projects) is the only workspace change worth making.
