# Brief — gridiron: play_log Multi-Player Attribution

**Role:** brief
**Sequence:** add-feature
**Date:** 2026-06-23

---

## Project Name
`gridiron-play-log-attribution`

## Description
Extend the `play_log` table and simulation engine to record the full cast of players involved in each play — QB, tackler, OL blocker, DL defender, and LB — enabling tackle leaders, OL grades, DL pressure stats, and complete pass attribution to be queried directly from `play_log`.

## Language(s)
Python (SQLAlchemy migration + engine changes) — no frontend changes in scope.

## Success Criteria

Done when:
1. Alembic migration adds 5 nullable FK columns to `play_log`: `secondary_player_id`, `tackler_player_id`, `ol_player_id`, `dl_player_id`, `lb_player_id`
2. `POSITION_GROUPS` in `constants.py` includes `"OL": ["LT", "LG", "C", "RG", "RT"]` — activating 2,080 OL players currently dropped by the roster loader
3. `PlayOutcome` carries all 5 new fields
4. `play_resolver.py` picks OL/DL/LB players on every run and pass play and assigns them to the correct `PlayOutcome` fields
5. `game.py` writes all 5 new columns to the `play_log` INSERT
6. After a game runs, a sample SQL query confirms:
   - `PASS_COMPLETE` rows: `secondary_player_id` = QB, `ol_player_id` non-null, `dl_player_id` non-null
   - `RUSH` rows: `tackler_player_id`, `ol_player_id`, `dl_player_id`, `lb_player_id` non-null
   - `SACK` rows: `secondary_player_id` = QB, `ol_player_id` = missed blocker

## Constraints

- Engine files (`gridiron/engine/`) are gitignored — changes are disk-only, never committed
- Existing 25k play_log rows are NOT backfilled (new columns stay NULL for old rows)
- Must not break the live simulation loop — changes are additive only
- `player_game_stats` table is NOT extended in this sprint (aggregation deferred)
- No new API endpoints or frontend changes in scope

## Out of Scope

- Backfilling historical play_log rows
- New `player_game_stats` columns for OL blocks, DL pressures, LB tackles
- Frontend stat displays consuming the new columns
- New API routes exposing per-play attribution data
- PAT / TWO_POINT_CONVERSION play attribution

## Assumptions

- OL snap-weight scoring uses same formula as other groups: `sigma * 0.4 + alpha * 0.3 + psi * 0.3`, top 3 by score, weights `[0.65, 0.225, 0.125]`
- For RUSH plays: `tackler_player_id` = `dl_defender or lb_defender`; TURNOVER_FUMBLE overrides tackler with `def_slot` (existing fumble recoverer)
- For SACK: `primary_player_id` remains the sacker; `secondary_player_id` = QB; `ol_player_id` = OL who missed block; `dl_player_id` = same as primary (intentional redundancy for query convenience)
- `lb_player_id` populated on RUSH plays only
- CB/DB coverage on PASS_COMPLETE captured via `tackler_player_id` (DB who closes after catch)

## Handoff

**Next role:** planner

Planner should:
1. Confirm the full field-assignment table per play type (which player slot → which `PlayOutcome` field for each of the ~10 play types)
2. Confirm snap-weight approach for OL — same formula as skill positions, or separate blocking-grade score?
3. Flag any play types where the same player ends up in two slots (e.g. SACK: sacker = `primary_player_id` AND `dl_player_id`) and decide whether to keep or deduplicate
4. Define exact order of `_pick()` calls within `resolve_play()` to minimise redundant roster sampling
5. Draft the `accumulate_stats` extension design for the follow-up sprint so the implementer can see where this is heading
