# Gridiron Sprint Review — sim_runs infrastructure (2026-06-26)

**Verdict: PASS WITH NOTES**

---

## Review Scope

Sprint delivered three units:
- `alembic/versions/e6f7a8b9c0d1_sim_runs.py` — migration
- `gridiron/orchestrator.py` — orchestrator updates
- 10 files across `gridiron/api/` — sim-runs management API + router filtering

Reviewed via: code read, live endpoint testing against `http://localhost:8006`, DB inspection via docker exec.

---

## Endpoint Verification

All major data endpoints return valid, scoped data from sim_run_id=1:

| Endpoint | Result |
|---|---|
| `GET /games?limit=3` | 1570 total games, correct data |
| `GET /games/1` | Valid game detail |
| `GET /schedule/week/1` | Valid week 1 schedule |
| `GET /schedule/current` | Returns week 2 (first live/scheduled week) |
| `GET /programs` | 130 programs with correct W-L records |
| `GET /programs/1/schedule` | Valid program schedule, sim_run_id scoped |
| `GET /leaderboards` | Valid top-10 stat leaders |
| `GET /nafca/leaderboard` | Returns data (see notes on pre-existing duplicate bug) |
| `GET /conglomerates/1/standings` | Valid tier1/tier2 standings |
| `GET /coaches/1` | Valid coach detail with season stats |
| `GET /players/1` | Valid player detail with bio |
| `GET /health` | `{"status":"ok"}` |

---

## sim-runs Management Endpoints

### GET /sim-runs
Returns list ordered by id DESC. Works correctly. With only run 1 present, returns a single entry.

### POST /sim-runs
Created a test run (id=2, label=test-review-run, status=running). Returns 201 with correct body including `production_id: null`, `production_name: null`.

**Side effect observed:** Once run 2 was created, `active_sim_run_id()` picked it as the active run (highest non-discarded id DESC), causing all data endpoints to return empty results for the duration. This is correct behavior but is a meaningful operational risk: creating any new sim_run immediately shadows all existing data in the API. There is no "draft" state or transition guard.

### PATCH /{id}/promote
Tested on id=2. Sets `production_id` and `production_name` and changes `status` to `complete`. Returns 200 with updated row. Works correctly.

After promotion, the production branch of `active_sim_run_id()` picks run 2 (it has `production_id` set), so the promoted empty run is still active — data endpoints still return zero results while a promoted empty run is active.

### DELETE /{id}
- Correctly blocks deletion of run 2 after promotion (has `production_id` set) → returns 400.
- Correctly deletes run 3 (no `production_id`, no games) → 204, no rows remain, game data unaffected.
- Cascade chain verified: `sim_runs → games (ON DELETE CASCADE) → play_log, player_game_stats (ON DELETE CASCADE)`.

Test state was cleaned up: run 2 was cleared via direct DB update then deleted via API. System restored to run 1 only.

---

## active_sim_run_id Logic

```sql
COALESCE(
    (SELECT id FROM sim_runs WHERE production_id IS NOT NULL ORDER BY production_id DESC LIMIT 1),
    (SELECT id FROM sim_runs WHERE status != 'discarded' ORDER BY id DESC LIMIT 1)
)
```

**With only run 1 (status=complete, production_id=NULL):**
- Production branch returns NULL.
- Fallback branch returns id=1.
- Correct: run 1 is served as active.

**Logic is correct for the intended use cases.** However, the `status != 'discarded'` guard in the fallback branch is dead code — there is no API path that sets a run to `status='discarded'`. The DELETE endpoint hard-deletes rather than soft-deletes. If a soft-delete workflow is ever added, the guard is ready; for now it is inert.

---

## Orchestrator Correctness

`season_loop` at startup:
```python
run_id = _active_sim_run_id(session.connection())
# SELECT id FROM sim_runs WHERE status = 'running' ORDER BY id DESC LIMIT 1
if run_id is None:
    logger.info("No running sim run found — season_loop exiting.")
    return
```

With run 1 at `status='complete'`, no run has `status='running'` → `_active_sim_run_id` returns `None` → `season_loop` logs and returns cleanly. No crash, no hang.

Note the intentional distinction: the orchestrator's `_active_sim_run_id` (sync, checks `status='running'`) is separate from the API's `active_sim_run_id()` (async, picks latest production or non-discarded). These serve different purposes and are correctly separate.

---

## Issues Found

### Note 1 — Safety gap: DELETE has no game-count guard
The `DELETE /sim-runs/{id}` guard is: `WHERE id=:id AND production_id IS NULL`.

Run id=1 has `production_id=NULL` and contains 1570 games. Calling `DELETE /sim-runs/1` would succeed, cascade-delete all 1570 games (and all play_log + player_game_stats rows via cascade). There is no guard against deleting a run that has game data, and no guard ensuring at least one sim_run always exists.

**Severity:** Medium. Currently harmless in practice (run 1 is the only run and no one calls this in production), but a single bad API call would wipe the entire dataset irreversibly.

**Suggested fix (optional):** Add a check in the delete handler: refuse if the run has any games (`SELECT 1 FROM games WHERE sim_run_id=:id LIMIT 1`), or refuse if it is the last non-discarded run.

### Note 2 — Creating a new sim_run immediately displaces all data endpoints
As observed during testing: `active_sim_run_id()` picks the highest-id non-discarded run. The moment a new run is created (even in draft/running state with zero games), all data endpoints return zero results. This may be intended behavior, but it means there is no safe way to "prepare" a new run while keeping the production data live.

**Severity:** Low (operational awareness issue, not a bug). No change needed unless a draft workflow is desired in future.

### Note 3 — `GET /live/leaders` missing sim_run_id filter (pre-existing)
`_LIVE_LEADER_QUERY` in `leaderboards.py` joins to `games` but does not filter by `sim_run_id`. It filters by `g.status = 'live'` only. In a multi-run scenario with two concurrent live games from different runs, leaders from all runs would be mixed.

This is a pre-existing gap (the query existed before this sprint; the sprint correctly added `sim_run_id` to `_LEADER_QUERY` but not `_LIVE_LEADER_QUERY`).

**Severity:** Very low (live games from multiple runs simultaneously is an edge case not yet supported operationally).

### Note 4 — `/nafca/leaderboard` returns duplicate programs (pre-existing)
The `_ELO_RANK_SQL` CTE (`fg`) produces two rows per program (one from the home branch `rn=1`, one from the away branch `rn=1`). The `LEFT JOIN fg ON fg.program_id = p.id` then matches both, producing 252 entries for 130 programs. Observed live: every active program appears twice.

This bug predates this sprint — it existed in the `season=1` version too (same CTE structure, same LEFT JOIN). The sprint correctly added `sim_run_id` filtering but did not introduce or fix this issue.

**Severity:** Bug (cosmetic/functional), pre-existing. Out of scope for this sprint.

---

## Migration Correctness

- `sim_runs` table created with correct columns, constraints, index.
- Run 1 seeded as `('alpha-001', 1, 'complete')` before FK addition.
- `games.sim_run_id` added nullable → backfilled → NOT NULL → FK with ON DELETE CASCADE. Correct approach for zero-downtime-friendly migration.
- `play_log.game_id` and `player_game_stats.game_id` FKs dropped and recreated with CASCADE. Verified in DB: all three cascade chains present.
- Downgrade restores original constraints. Downgrade is correct.

---

## Router Coverage Summary

All 6 data routers updated correctly:

| Router | sim_run_id filtered |
|---|---|
| `games.py` | Yes — list_games |
| `schedule.py` | Yes — current + week queries |
| `programs.py` | Yes — W-L CTE, stat queries, program schedule |
| `coaches.py` | Yes — coach season stats |
| `leaderboards.py` | Yes — stat leaders; live leaders omitted (pre-existing) |
| `nafca.py` | Yes — ELO rank queries |
| `conglomerates.py` | Yes — W-L CTE, standings queries |

Static endpoints (roster, player bio, conglomerate list, coach profile) correctly do not filter by sim_run_id — they are sim-run-agnostic data.

---

## Verdict: PASS WITH NOTES

The sprint is functionally correct. All three units delivered working code. The migration is safe. The orchestrator exits cleanly when no running sim run exists. The 10 router files are all correctly updated to use `active_sim_run_id()`. The management endpoints work as specified.

The one actionable note for this sprint: the DELETE endpoint should guard against deleting runs with game data (Note 1). Notes 2, 3, and 4 are either pre-existing or operational awareness items that do not block shipping.
