# Brief — gridiron: Defensive Position Expansion + Pass Rush Pre-Picks

**Role:** brief
**Sequence:** add-feature
**Date:** 2026-06-23

---

## Project Name
`gridiron-defensive-positions`

## Description

Expand the defensive position taxonomy from 4 generic codes (OLB, MLB, CB, S) to 7 specific codes (LOLB, MLB, ROLB, CB, DB, SS, FS), migrate existing players, and restructure `POSITION_GROUPS` so the engine can address each defensive unit independently. Add LB and secondary pre-picks to pass plays in `play_resolver.py`. This lays the foundation for zone-based defensive formation matchups in a future sprint.

## Language(s)
Python (Alembic migration + seed_roster.py update + engine constants + play_resolver change) — no frontend changes.

## Success Criteria

Done when:
1. Alembic migration reassigns existing players: `OLB` split evenly → `LOLB` / `ROLB` (by player_id parity); `S` split evenly → `SS` / `FS` (by player_id parity); existing `CB` and `MLB` unchanged.
2. `seed_roster.py` `POSITION_DISTRIBUTION` updated to use new codes: `LOLB`, `ROLB`, `MLB`, `CB`, `DB`, `SS`, `FS`. New template still sums to 85. `JERSEY_RANGES` updated for all new codes.
3. `POSITION_GROUPS` in `constants.py` updated:
   - `"LB": ["LOLB", "MLB", "ROLB"]`
   - `"DB": ["CB", "DB"]` (CB = corners; DB = nickel/slot)
   - `"S":  ["SS", "FS"]`
4. `PlayOutcome` in `play_resolver.py` carries `lb_player_id` and `s_player_id` (nullable) in addition to existing `tackler_player_id`, `ol_player_id`, `dl_player_id`.
5. PASS block in `play_resolver.py` pre-picks `lb_rusher = _pick(defense.get("LB", []))` and `s_coverage = _pick(defense.get("S", []))` alongside existing `dl_rusher` and `ol_blocker`.
6. `lb_player_id` populated on PASS plays where LB is involved (SACK if sacker is LB, PASS_COMPLETE as secondary coverage, PASS_INCOMPLETE/DEFLECTION as pass rusher).
7. `s_player_id` populated on deep pass plays (PASS_COMPLETE, TURNOVER_INTERCEPTION) as the deep coverage player.
8. Alembic migration adds `s_player_id` column to `play_log` (joining the 5 from previous sprint).
9. After migration + one game run: `SELECT position, COUNT(*) FROM players GROUP BY position` shows LOLB, ROLB, SS, FS, CB, DB (if seeded), MLB rows. `play_log` shows non-null `lb_player_id` on SACK rows and non-null `s_player_id` on PASS_COMPLETE rows.

## Constraints

- Engine files (`gridiron/engine/`) are gitignored — changes are disk-only, never committed
- `seed_roster.py` and Alembic migrations ARE tracked — commit them
- Migration must be additive/safe: split is deterministic (player_id parity), no data loss
- `player_game_stats` NOT extended in this sprint
- No frontend changes
- The 85-player roster template must still sum to 85 after position code changes
- `DB` (nickel/slot) is a NEW position code — no existing players have it post-migration; it will appear in future seeded rosters only

## Out of Scope

- Zone-based formation grid (3×3 field zones) — future sprint
- Formation definitions that shift player zone weights — future sprint
- New `player_game_stats` columns for LB pressures, S coverage grades, DB targets
- Any changes to OL, DL, QB, RB, WR, K, P position codes

## Assumptions

- OLB split: player_id % 2 == 0 → LOLB, player_id % 2 == 1 → ROLB
- S split: player_id % 2 == 0 → SS, player_id % 2 == 1 → FS
- `DB` nickel/slot position code: 0 existing players (new code for future rosters); add to POSITION_DISTRIBUTION with count=1 in reserve slot, replacing one "CB" reserve
- New roster distribution: LOLB=3, ROLB=3, MLB=4, CB=6, DB=1, SS=3, FS=3 (total def secondary/LB = 23, same as before: OLB=6→LOLB3+ROLB3, MLB=4, CB=7→CB6+DB1, S=6→SS3+FS3)
- `lb_rusher` and `s_coverage` are new pre-picks; existing `tackler_player_id` on PASS_COMPLETE (DB closer) is renamed to `db_player_id` for consistency — this is a `play_log` column rename requiring a new migration step
- SACK attribution: if sacker came from LB pool, `lb_player_id` = sacker, `dl_player_id` = NULL; if from DL pool, existing behaviour. Since pre-sprint SACK picks from `DL or LB` pool without knowing which, post-sprint SACK pre-picks DL and LB separately: dl_sacker is pre-picked, lb_sacker is pre-picked, primary_player_id = whichever has higher snap_weight (or dl_sacker if both non-null by convention)

## Handoff

**Next role:** planner

Planner should:
1. Confirm the exact position counts in the new POSITION_DISTRIBUTION (must sum to 85)
2. Decide whether the `tackler_player_id` rename to `db_player_id` is worth the migration cost, or whether keeping the existing name is less disruptive
3. Confirm the SACK attribution approach — pre-pick both DL and LB, winner = dl_sacker by convention, lb_player_id = lb_sacker always
4. Confirm `s_player_id` column naming and which play types it populates
5. Map all play types to all attribution columns (the full field-assignment table, updated)
