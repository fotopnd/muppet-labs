# Retro — gridiron: sim_runs infrastructure (2026-06-26)

**Role:** retro
**Sequence:** feature-sprint (3 serial units)
**Date:** 2026-06-26

---

## Project

`gridiron-sim-runs-infrastructure` — `feature-sprint` sequence. 3 serial units: migration → orchestrator → API. All three units completed and merged. Reviewer verdict: PASS WITH NOTES (4 notes; Note 1 delete guard was fixed post-review before this retro ran). No deploy — localhost alpha tuning sprint.

Context: the sim_runs table is the foundation for running alpha seasons to tune engine constants before promoting Season 1 to production. Without it, every game in the DB belongs to an unscoped, unmanageable blob. This sprint makes it possible to create, run, inspect, promote, and delete simulation runs cleanly.

---

## What Went Well

**W1 — Serial dependency chain was the right call:** Unit 01 (migration) had to land before 02 and 03 could touch the DB. The manifest correctly kept all three units serial rather than attempting parallelism. No unit blocked on another's unfinished work at any point.

**W2 — Migration approach was correct:** The migration used the safe pattern for adding a NOT NULL FK to an existing table: add nullable → backfill → set NOT NULL → add FK with cascade. Cascade chains for `games → play_log` and `games → player_game_stats` were also correctly tightened in the same migration. The reviewer verified all three cascade chains live via `\d games` and confirmed downgrade was correct.

**W3 — Two distinct `active_sim_run_id` functions, correctly separated:** The orchestrator's sync version (checks `status='running'`) and the API's async version (picks latest production or non-discarded) serve different purposes. Keeping them separate was the right design and avoided introducing coupling between the sim control plane and the data serving layer. The reviewer called this out as correct, not a duplication smell.

**W4 — Live runtime verification produced a real finding (Note 1):** The reviewer called `DELETE /sim-runs/{id}` on a run with games and observed no guard. This is exactly what live endpoint testing is for — it found a gap the code review alone would not have surfaced. The fix (game-count check before delete) was applied post-review.

**W5 — Clean sprint, minimal scope:** 3 units, all within the defined file list, no spillover into unrelated routers. The sprint manifest's `Files owned` table was accurate — unit 03 owned exactly the 10 files listed and no others needed touching.

---

## What Could Have Gone Better

**B1 — `status='discarded'` guard is dead code:** The `active_sim_run_id()` fallback in the API has `WHERE status != 'discarded'` but there is no API path that sets a run to `status='discarded'`. The DELETE endpoint hard-deletes. This dead guard was not introduced by this sprint (it's intentional defensive code), but the brief and planner did not note it. If a soft-delete path is ever added, this becomes active — it should be in project-state.md as a known design decision, not silently inert.

**B2 — No "draft" state design, but operational gap is real:** Creating a new sim_run immediately shadows all data endpoints for the current API. This was caught by the reviewer (Note 2) during live testing. It was not in the brief as a known limitation. A brief for any sprint that adds run management should explicitly state the active-run selection semantics so the implementer understands the operational consequences of each state transition.

**B3 — Two pre-existing bugs surfaced during review:** Notes 3 and 4 (`_LIVE_LEADER_QUERY` missing sim_run_id filter; `/nafca/leaderboard` duplicate programs CTE bug) were flagged as pre-existing but discovered during this sprint's review. Neither blocked the PASS verdict, but they are now logged. Future sprints should check whether known pre-existing bugs are in project-state.md before the reviewer finds them fresh.

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| Unit 03 (API) | Agent read all 7 router files cold to understand existing query patterns before adding `sim_run_id` filters — no pattern example was in the brief | Medium | Brief should include a single representative query pattern (one existing CTE example + the `active_sim_run_id()` call signature) so the agent doesn't need to reverse-engineer it from 7 files |
| Sprint review | Reviewer loaded full sprint manifest to understand scope — the manifest includes two separate sprint tables (bug-fixes and sim_runs) in the same file | Low | Sprint manifest output.md should scope to one sprint per file, or retro/review should be pointed at a specific sprint section heading |
| Retro (this session) | Retro loaded sprint-planner output.md which contains 3 sprint manifests — only the sim_runs one was relevant | Low | Sprint planner should write one output file per sprint, not append to a rolling manifest |

### Redundancy Patterns

- The `active_sim_run_id()` async function pattern was introduced in unit 01 (`sim_run.py`) and then referenced in 7 router files in unit 03. The brief for unit 03 should have included the exact import and call signature so the agent doesn't scan `sim_run.py` to find it.
- The reviewer re-read `sim_run.py` to understand the `active_sim_run_id` logic before evaluating each router — this is unavoidable but could be shortened if the review brief included the function signature.

### Scoping Recommendations

- Unit 03 briefs for "add X to N routers" patterns should include: (a) the exact import line, (b) one before/after example query showing where `sim_run_id` is injected, (c) a checklist of which routers need it and which don't (static endpoints). This replaces cold reads of all N files.
- Sprint planner should write one manifest file per sprint run (e.g. `output-sim-runs-2026-06-26.md`) rather than appending all sprints to `output.md`. This scopes retro and reviewer context correctly.

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `_config/project-state.md` | Add `status='discarded'` guard note under gridiron known design decisions: "API `active_sim_run_id()` has `WHERE status != 'discarded'` guard — currently dead code (DELETE hard-deletes). Intentional hook for future soft-delete path." | Prevents future reviewers from flagging it as dead code without context | No |
| `_config/project-state.md` | Add pre-existing bugs section for gridiron: `_LIVE_LEADER_QUERY` missing sim_run_id filter (leaderboards.py); `/nafca/leaderboard` duplicate program rows (CTE structure) | These were surfaced in review; they should be tracked rather than re-discovered | No |

### Skills to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `skills/sprint-agent-handoff.md` | Add: "For 'add filter to N routers' units, the brief must include the exact import line, one before/after query example, and a checklist of which files need the filter vs which are static-data endpoints." | Prevents cold multi-file reads when the pattern is uniform | No |

### Routing Changes

| Sequence | Change | Reason | Human decision required? |
|----------|--------|--------|--------------------------|
| `feature-sprint` sprint-planner step | Add: "Write one manifest file per sprint, named `output-<slug>-<date>.md`. Do not append multiple sprints to `output.md`." | Scopes retro and reviewer inputs to the relevant sprint only | No |
| `feature-sprint` brief step | Add: "For management API units (create/update/delete endpoints on a resource), the brief must state the active-selection semantics and any operational side effects of each state transition." | Prevents operational gaps (like create-shadows-active) from being discovered only at review time | No |

### New Resources or Skills Needed

- None. The friction in this sprint was brief-quality and manifest-scoping, not missing knowledge resources.

---

## One Change to Make Now

**Sprint planner: write one manifest file per sprint.** The rolling `output.md` in `roles/sprint-planner/output/` now contains 3 separate sprint manifests, making retro and reviewer context unnecessarily broad. Change the sprint-planner routing step to write `output-<slug>-<date>.md` per sprint. This is the single cheapest structural fix that compounds across every future sprint — each downstream role (implementer, reviewer, retro) gets a correctly scoped input file with no extra effort.

---

## Handoff

Recommendations are notes only. The human applies changes to `_config/project-state.md`, `resources/routing.md`, and `skills/sprint-agent-handoff.md` if desired.

Suggested next step: run several alpha seasons to tune engine constants. When constants are stable, promote the alpha run to production and set Season 1 as the live run. The `POST /sim-runs`, `PATCH /{id}/promote`, and `DELETE /{id}` endpoints are all verified and ready.

Update `_config/project-state.md` to record: sim_runs infrastructure sprint complete (2026-06-26), retro complete, delete-guard fix applied post-review.
