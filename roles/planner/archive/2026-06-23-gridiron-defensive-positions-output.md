# Planner Output — gridiron: Defensive Position Expansion + Pass Rush Pre-Picks

**Role:** planner
**Sequence:** add-feature
**Date:** 2026-06-23

---

## Project

`gridiron-defensive-positions` — Expand defensive position taxonomy to 7 specific codes, migrate existing players, restructure `POSITION_GROUPS`, add LB and S pre-picks to pass plays, and add `s_player_id` column to `play_log`.

---

## Requirements

1. Alembic migration splits `OLB` → `LOLB` / `ROLB` (by `player_id % 2`) and `S` → `SS` / `FS` (by `player_id % 2`). Existing `CB` and `MLB` unchanged.
2. After migration: `SELECT position, COUNT(*) FROM players GROUP BY position` shows LOLB, ROLB, SS, FS, CB, MLB — no OLB or S rows remain.
3. `seed_roster.py` `POSITION_DISTRIBUTION` uses new codes. Template still sums to 85. `JERSEY_RANGES` covers all new codes.
4. `POSITION_GROUPS` updated: `"LB": ["LOLB", "MLB", "ROLB"]`, `"DB": ["CB", "DB"]`, `"S": ["SS", "FS"]`.
5. Alembic migration adds `s_player_id` (nullable FK → `players.id`) to `play_log`. (`tackler_player_id` NOT renamed — not worth the migration cost.)
6. `PlayOutcome` carries `s_player_id` (in addition to the 5 existing attribution fields).
7. `game.py` writes `s_player_id` to the `play_log` INSERT.
8. PASS block in `play_resolver.py` pre-picks `lb_rusher = _pick(defense.get("LB", []))` and `s_coverage = _pick(defense.get("S", []))` alongside existing `dl_rusher` and `ol_blocker`.
9. `lb_player_id` populated on ALL pass plays (not just RUSH). SACK: convention is `dl_player_id` = primary (DL sacker wins), `lb_player_id` = lb_rusher (always set if non-null). Other pass plays: lb_rusher used as pass-rush attribution.
10. `s_player_id` populated on PASS_COMPLETE, TURNOVER_INTERCEPTION, PASS_DEFLECTION, PASS_INCOMPLETE (deep coverage player always present).
11. One game run after changes: `play_log` PASS_COMPLETE rows have non-null `lb_player_id` and `s_player_id`. RUSH rows unchanged.

---

## Decisions Made (planner-resolved from brief open questions)

**Q1 — `tackler_player_id` rename:** Do NOT rename. `tackler_player_id` is already written to 25k+ rows and consumed by queries. Adding a new column `s_player_id` is additive; renaming is destructive. The "DB closer on PASS_COMPLETE" stays in `tackler_player_id`. `s_player_id` is the deep safety coverage player, distinct from the tackle.

**Q2 — SACK attribution with dual pre-picks:** Pre-pick both `dl_rusher` and `lb_rusher` before roll. SACK outcome: `primary_player_id` = `dl_rusher` (convention — DL wins the sack credit; if DL pool is empty, fall back to `lb_rusher`). `dl_player_id` = same as primary (existing intentional redundancy). `lb_player_id` = `lb_rusher` always (even if LB didn't get the sack — they were rushing). This reflects that every pass play has both a DL and LB rushing component.

**Q3 — `s_player_id` naming:** `s_player_id` — references the `S` group (safeties). Distinct from `secondary_player_id` (which = QB on pass plays). No naming conflict.

**Q4 — New roster distribution (must sum to 85):**

Starters (75):
| Position | Count | Notes |
|---|---|---|
| QB | 3 | unchanged |
| RB | 4 | unchanged |
| FB | 2 | unchanged |
| WR | 8 | unchanged |
| TE | 4 | unchanged |
| LT | 3 | unchanged |
| LG | 3 | unchanged |
| C | 3 | unchanged |
| RG | 3 | unchanged |
| RT | 3 | unchanged |
| DE | 5 | unchanged |
| DT | 5 | unchanged |
| LOLB | 3 | was OLB(5) split |
| MLB | 4 | unchanged |
| ROLB | 2 | was OLB(5) split |
| CB | 6 | was CB(7) |
| DB | 1 | new nickel/slot code |
| SS | 3 | was S(5) split |
| FS | 2 | was S(5) split |
| K | 1 | unchanged |
| P | 2 | unchanged |
| LS | 1 | unchanged |
| ATH | 4 | unchanged |

Reserves (10): QB(1) RB(1) WR(2) ROLB(1) CB(1) DE(1) LT(1) FS(1) ATH(1)

Total per-position (starters + reserves):
LOLB=3, ROLB=3, MLB=4 | CB=7, DB=1 | SS=3, FS=3
LB total: 10 (was OLB+MLB=10 ✓) | Secondary total: 14 (was CB+S=14 ✓)

---

## Updated Field-Assignment Table (pass plays, new columns)

| `play_type` | `lb_player_id` | `s_player_id` |
|---|---|---|
| SACK | lb_rusher (always) | — |
| TURNOVER_INTERCEPTION | lb_rusher | s_coverage |
| PASS_COMPLETE | lb_rusher | s_coverage |
| PASS_TD (inline TOUCHDOWN row) | — | — |
| PASS_DEFLECTION | lb_rusher | s_coverage |
| PASS_INCOMPLETE | lb_rusher | s_coverage |
| RUSH / TFL / TURNOVER_FUMBLE | (existing — from RUSH pre-picks) | — |

---

## Technology Stack

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | existing project |
| Package manager | uv | existing project |
| Formatter/linter | ruff | existing project |
| Migration | Alembic | existing |
| Engine files | disk-only, gitignored | policy |

---

## Files Changed

| File | Tracked? | Change |
|------|----------|--------|
| `alembic/versions/<new>.py` | ✅ yes | Position split + `s_player_id` column |
| `scripts/seed_roster.py` | ✅ yes | New POSITION_DISTRIBUTION + JERSEY_RANGES |
| `gridiron/engine/constants.py` | ❌ gitignored | Updated POSITION_GROUPS |
| `gridiron/engine/play_resolver.py` | ❌ gitignored | New slots, pre-picks, updated returns |
| `gridiron/engine/game.py` | ❌ gitignored | `_to_row()` + INSERT extended |

---

## Open Questions for Architect

1. `DB` group: 1 player in rosters post-migration (only new seeds will have it). Does `_pick(defense.get("DB", []))` returning `None` for all existing games cause issues? It should not — `None` slots work, but confirm.
2. SACK fallback: if `dl_rusher` is None (empty DL pool — rare but possible), `primary_player_id` should fall back to `lb_rusher`. Architect confirms the fallback logic.
3. `ROLB` starters = 2 (vs LOLB = 3). Is this acceptable asymmetry or should we balance to LOLB=2+ROLB=3 or some other split? Impact on snap weights: top-3 selection still works with only 2 players in group (2 get weights [0.65, 0.225]).

---

## Handoff

**Next role:** architect

Architect reads this file plus `roles/brief/output/output.md`. Key work:
- Read `scripts/seed_roster.py`, `gridiron/engine/play_resolver.py`, `gridiron/engine/game.py`, `alembic/versions/a7b8c9d0e1f2_play_log_attribution.py` (the most recent migration) before writing specs
- Resolve the 3 open questions above
- Produce the exact POSITION_DISTRIBUTION list, migration SQL, and updated pass block code
