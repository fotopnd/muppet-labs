## Project Name
Gridiron

## Description
Wire the new coach attributes (`run_tendency`, `style`, `prestige`) into the simulation engine so that the OC and DC on each team actively shape play outcomes. OC influences play-type selection probabilities and offensive output distributions. DC influences which defensive personnel are picked and how many players occupy each defensive position group per play.

All files in this unit are gitignored (`gridiron/engine/`). Nothing is committed — the implementer edits the engine directly.

## Language(s)
Python (simulation engine — gitignored)

## Success Criteria

**OC influence:**
- The OC's `run_tendency` biases the RUSH vs PASS play-type selection probability. A `run_tendency` of 0.70 should produce noticeably more RUSH plays than 0.30 over a full game.
- OC `style` modifies output distributions:
  - `spread` / `air_raid`: higher pass yards variance, slightly elevated INT risk
  - `power_run`: higher short-yardage RUSH success probability; lower RUSH yards variance
  - `west_coast`: elevated PASS_COMPLETE rate on short routes (lower yards, higher completion)
  - `balanced`: no modifier (current behaviour)

**DC influence:**
- The DC's `style` determines the defensive personnel grouping used for each play:
  - `4-3`: select up to 4 DL, 3 LB, 4 DB on each play
  - `3-4`: select up to 3 DL, 4 LB, 4 DB
  - `nickel`: select up to 3 DL, 2 LB, 5 DB
  - `blitz_heavy`: select up to 4 DL, 4 LB, 3 DB; +15% sack probability modifier on pass plays
- Personnel picks use the existing `_pick()` helper with the appropriate position group pools from `POSITION_GROUPS`
- If a position group pool is smaller than the target count, pick all available (no error)

**Verification:**
- Run a full game via `sim-sandbox` or equivalent
- Check play_log: RUSH play share should vary between a `run_tendency=0.30` team and `run_tendency=0.70` team
- Check that `dl_player_id`, `lb_player_id`, `s_player_id` attribution columns reflect the DC's formation (e.g. nickel teams produce more DB picks)

## Constraints
- Load OC and DC from the coaches table at game-start alongside the roster. Filter by `role = 'OC'` and `role = 'DC'` for each program.
- OC/DC attributes must be loaded once per game (not per play) and passed into the resolver or stored on the game state object.
- `run_tendency` blending: use it as a weight in the existing play-type probability selection. Do not hardcode absolute thresholds — blend with the existing probability table.
- Style modifiers should be mild (±5–15% adjustments). Do not override the core probability model.
- Prestige is NOT wired into the engine in this unit — it is a future recruiting mechanic.
- Do not add new DB columns in this unit (schema is done in unit 02).

## Out of Scope
- `alembic/` — no migrations
- `gridiron/api/` — no API changes
- `web/` — no frontend changes
- Prestige effect on recruiting — deferred
- `boosters` table influence — deferred

## Assumptions
- Unit 02 (coach-attributes-schema) is merged before this unit runs — the three new columns exist in the DB
- Engine files are at `gridiron/engine/game.py`, `gridiron/engine/play_resolver.py`, `gridiron/engine/constants.py` (all gitignored)
- `POSITION_GROUPS` in `constants.py` has keys: QB, RB, WR, OL, DL, LOLB, ROLB, MLB, CB, SS, FS (or similar — check at runtime)
- The `_pick()` function accepts a list of player objects and returns one (or None if empty)
- Coaches are accessible via the DB session already open in `game.py`

## Handoff
Engine changes are live immediately (no deploy needed — local sim). Run a game via sim-sandbox and confirm play_log attribution reflects DC formation choices. This unit is parallel with unit 04.
