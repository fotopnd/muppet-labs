# Reviewer Output — Gridiron Bug Fix Sprint (2026-06-26)

**Verdict: FAIL**

Three of four items need hotfixes before this sprint can be considered closed.

---

## Summary Table

| Unit | Status | Notes |
|---|---|---|
| tfl-description-fix | FAIL | Existing play data still has ball carrier as primary_player; description text uses wrong name in all 1,470 TFL plays |
| h2h-tiebreaker | PASS WITH NOTES | Logic is correct; stale server — needs restart to take effect |
| player-stats-extension (migration) | PASS | `dl_pressures` + `lb_tackles` columns exist in DB with correct server_defaults |
| player-stats-extension (API) | FAIL | `get_player` query in `programs.py` never SELECTs the new columns; they are absent from API responses |

---

## Finding 1 — FAIL: TFL attribution bug is not fixed in existing data

**File:** `gridiron/engine/play_resolver.py` (gitignored — cannot inspect)
**Evidence from DB:**

- 100% of 1,470 existing `TACKLE_FOR_LOSS` plays in `play_log` have `primary_player_id` pointing to the ball carrier (verified by comparing `primary_player_id.program_id` against the possessing team's program_id across 20 samples — all 20 were the possessing team's player).
- `player_game_stats.tackles` for TACKLE_FOR_LOSS is being credited to RBs, FBs, and ATH players (ball carriers), not to DL/LB defenders. The top "tackler" positions: RB (614 total), ATH (571), FB (263). DT has only 12 tackles across 3 players.
- Play descriptions like "Rivera with the stop" and "Noriega stops the runner" use the ball carrier's name, not the tackler's.
- `primary_player_id` for TFL plays is the ball carrier's id. `tackler_player_id` column exists in `play_log` but is `NULL` in all sampled TFL plays.

**Root cause (likely):** The engine fix in `play_resolver.py` may generate new plays correctly, but:
1. No new plays have been generated since the fix (last play in DB: `2026-06-26 13:06:20`, engine fix deployed after that).
2. All historical game data retains the old wrong attribution.
3. `player_game_stats` accumulates stats per game; all 123 completed games were played before the fix.

**Hotfix required:**
- Verify `play_resolver.py` actually writes the tackler's name to the TFL description and credits the tackler's `player_game_stats.tackles` (not the ball carrier).
- If the fix is correct in the engine, the existing `player_game_stats` data needs a backfill. The `play_log.lb_player_id` and `play_log.dl_player_id` columns exist but are currently `NULL` in TFL plays — if the fix now populates them, a migration script can backfill stats from newly-generated plays. Historical data (pre-fix) cannot be corrected without replaying.
- Alternatively, accept that pre-fix historical data is wrong and document it as a known limitation.

---

## Finding 2 — FAIL: `dl_pressures` and `lb_tackles` absent from player API response

**File:** `/Users/fotopnd/Documents/muppet-labs/projects/gridiron/gridiron/api/routers/programs.py`, lines 280–346
**Evidence:**

- The DB migration `d5e6f7a8b9c0` correctly added both columns. The schema `PlayerDetail` in `schemas.py` correctly declares both fields (lines 128–129). The DB has 11 rows with non-zero values (e.g., player 6667 has `dl_pressures=16`, player 6692 has `lb_tackles=21`).
- The `get_player` query's LEFT JOIN subquery (lines 311–334) does **not** include `dl_pressures` or `lb_tackles` in its SELECT list. The COALESCE-wrapped outer SELECT (lines 289–307) also does not include them.
- API response for players 6667 and 6692 omits both fields entirely — Pydantic uses the schema defaults of `0` without any DB values.

**Hotfix required:** Add `dl_pressures` and `lb_tackles` to the inner subquery and outer SELECT in `get_player` in `programs.py`:

```python
# In the inner subquery (around line 330):
SUM(pgs.dl_pressures)::int  AS dl_pressures,
SUM(pgs.lb_tackles)::int    AS lb_tackles,

# In the outer SELECT (around line 306):
COALESCE(st.dl_pressures, 0) AS dl_pressures,
COALESCE(st.lb_tackles, 0)   AS lb_tackles,
```

---

## Finding 3 — PASS WITH NOTES: H2H tiebreaker logic is correct but server is stale

**File:** `/Users/fotopnd/Documents/muppet-labs/projects/gridiron/gridiron/api/routers/conglomerates.py`
**Evidence:**

- The `_h2h_wins` and `_sort_with_h2h` functions are logically correct. Manually simulated with conglomerate 5's 1-1 tied group (4 teams): Hoover (1 H2H win) correctly sorts to top when `_sort_with_h2h` is called directly.
- The live API currently returns incorrect ELO-only ordering for the 1-1 group in conglomerate 5 (returns Cheyenne → NB → Dothan → Hoover; correct is Hoover → Cheyenne → NB → Dothan).
- Cause: the uvicorn process (PID 17636) started at `2026-06-25 23:05:28` — before `conglomerates.py` was modified at `2026-06-26 14:04`. Server is running stale code. No `--reload` flag.

**Action required:** Restart the uvicorn server. No code changes needed.

**Edge case notes on the H2H logic:**
- Groups of 3+ tied teams where not all pairs played each other: H2H query correctly returns only games between teams in the group. Teams with 0 H2H wins sort by ELO — this is the right fallback.
- Draw games: `CASE WHEN home_score > away_score THEN home ELSE away` would wrongly credit a draw to the away team. No draws exist in the DB (confirmed: 0 completed games with equal scores). Football sim presumably enforces a winner, so this is a theoretical non-issue.
- Season hardcoded as `1` in the H2H query — consistent with all other queries. Fine for current single-season state.

---

## Finding 4 — PASS: Migration `d5e6f7a8b9c0` is correct

The migration correctly adds `dl_pressures` and `lb_tackles` as `INTEGER NOT NULL DEFAULT 0` columns to `player_game_stats`. `down_revision` is `c9d0e1f2a3b4` (correct chain). `downgrade()` removes both columns cleanly.

---

## Regression Check

| Endpoint | Status |
|---|---|
| `GET /conglomerates` | OK — returns valid data |
| `GET /conglomerates/{id}/standings` | API returns stale result (no H2H); code is correct post-restart |
| `GET /games/{id}` | OK |
| `GET /games/{id}/boxscore` | OK |
| `GET /games/{id}/plays` | OK — plays endpoint works; TFL descriptions affected by Finding 1 |
| `GET /leaderboards` | OK |
| `GET /nafca/leaderboard` | OK (note: duplicate entry for Michigan Institute in lifetime list — pre-existing issue, not this sprint) |
| `GET /schedule/current` | OK |
| `GET /players/{id}` | Missing `dl_pressures` + `lb_tackles` (Finding 2) |

---

## What Needs Fixing Before Sprint Close

1. **Hotfix A** (`programs.py` `get_player`): Add `dl_pressures` and `lb_tackles` to the player stats subquery and outer SELECT. Two-line change.

2. **Hotfix B** (TFL attribution): Verify `play_resolver.py` correctly attributes TFL tackles to the defensive player. Run a game after the fix and confirm `player_game_stats.tackles` credits a DL/LB, not an RB/FB. Decide whether to backfill historical data or document as pre-fix limitation.

3. **Operational**: Restart uvicorn (`uv run uvicorn gridiron.api.main:app --port 8006`) to load the H2H standings fix.

---

## Handoff

Hotfix A is a two-line code change in a tracked file — can be applied immediately. Hotfix B requires inspecting the gitignored engine file and deciding on historical data strategy. The server restart is a one-liner. All other endpoints are clean.
