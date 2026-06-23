# Planner Output — gridiron: play_log Multi-Player Attribution

**Role:** planner
**Sequence:** add-feature
**Date:** 2026-06-23

---

## Project

`gridiron-play-log-attribution` — Extend `play_log` with 5 nullable FK columns capturing the full player cast per play, and activate 2,080 OL players currently dropped by the roster loader.

---

## Requirements

1. `alembic upgrade head` applies a migration that adds 5 nullable integer FK columns to `play_log`: `secondary_player_id`, `tackler_player_id`, `ol_player_id`, `dl_player_id`, `lb_player_id` — all referencing `players.id`.
2. Rows in `play_log` created before the migration have NULL in all 5 new columns (no backfill).
3. `POSITION_GROUPS` in `gridiron/engine/constants.py` contains `"OL": ["LT", "LG", "C", "RG", "RT"]`, causing OL players to enter `build_roster_map`.
4. `PlayOutcome` carries all 5 new fields as `int | None`, defaulting to `None`.
5. After a game runs, `play_log` rows satisfy the field-assignment table below for each play type — no new column is NULL when a matching player was available in the roster.
6. The existing game loop is not broken — all new fields are optional, no existing INSERT columns are removed or renamed.
7. `player_game_stats` is NOT extended (aggregation deferred).

---

## Field-Assignment Table (per play type)

| `play_type` | `secondary_player_id` | `tackler_player_id` | `ol_player_id` | `dl_player_id` | `lb_player_id` |
|---|---|---|---|---|---|
| `RUSH` | — | dl_defender OR lb_defender | OL blocker | DL defender | LB defender |
| `RUSH_TD` | — | dl_defender OR lb_defender | OL blocker | DL defender | LB defender |
| `TFL` | — | def_slot (existing tackler) | OL blocker | DL defender | LB defender |
| `TURNOVER_FUMBLE` | rusher (ball carrier) | def_slot (fumble recoverer — overrides tackler pick) | OL blocker | DL defender | LB defender |
| `PASS_COMPLETE` | QB | DB/LB closer (new pick) | OL blocker | DL rusher | — |
| `PASS_TD` | QB | DB/LB closer (new pick) | OL blocker | DL rusher | — |
| `PASS_INCOMPLETE` | QB | — | OL blocker | DL rusher | — |
| `PASS_DEFLECTION` | QB | — | OL blocker | DL rusher | — |
| `SACK` | QB | — | OL missed blocker | DL rusher (= primary_player_id) | — |
| `TURNOVER_INTERCEPTION` | QB | — | OL blocker | DL rusher | — |
| Special teams (FG, PAT, PUNT, KICKOFF, TWO_POINT) | — | — | — | — | — |

**SACK redundancy:** `dl_player_id = primary_player_id` on SACK rows — intentional. Lets queries join `dl_player_id` across all pass plays without a UNION. Mark with a comment in the code.

---

## OL Snap-Weight Formula

Same formula as all other position groups: `sigma * 0.4 + alpha * 0.3 + psi * 0.3`. Top 3 by score, weights `[0.65, 0.225, 0.125]`. No separate blocking grade this sprint. OL-specific grading deferred to the follow-up.

---

## `_pick()` Call Order in `resolve_play()`

Pick once before the probability roll — results are shared across all outcome branches for that play.

**RUSH plays:**
```python
ol_blocker  = _pick(offense.get("OL", []))
dl_defender = _pick(defense.get("DL", []))
lb_defender = _pick(defense.get("LB", []))
tackler     = dl_defender or lb_defender
```

**PASS plays:**
```python
# qb = _pick(...) already exists in current code
ol_blocker = _pick(offense.get("OL", []))
dl_rusher  = _pick(defense.get("DL", []))
```
Then per-outcome only for PASS_COMPLETE / PASS_TD:
```python
db_closer = _pick(defense.get("DB", []) or defense.get("LB", []))
```

---

## Technology Stack

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | existing project |
| Package manager | uv | existing project |
| Formatter/linter | ruff | existing project |
| Migration | Alembic | existing project |
| ORM | SQLAlchemy raw `text()` | existing project pattern |
| Engine files | disk-only, gitignored | policy constraint |

---

## Files Changed

| File | Tracked? | Change |
|------|----------|--------|
| `gridiron/engine/constants.py` | ✅ yes | Add `"OL"` key to `POSITION_GROUPS` |
| `alembic/versions/<new>.py` | ✅ yes | 5 nullable FK columns on `play_log` |
| `gridiron/engine/play_resolver.py` | ❌ gitignored | `PlayOutcome` slots + new `_pick()` calls |
| `gridiron/engine/game.py` | ❌ gitignored | 5 new columns in `play_log` INSERT |

---

## accumulate_stats Extension (follow-up sprint note — not in scope)

When `player_game_stats` is extended, add these counters to `accumulate_stats`:
- `ol_player_id` → increment `blocks`
- `dl_player_id` → `pressures` (PASS plays), `run_stops` (RUSH plays)
- `lb_player_id` → `run_stops`
- `tackler_player_id` → `tackles`

Requires new `player_game_stats` columns. Migration deferred.

---

## Open Questions for Architect

1. **`_pick()` on empty-weight list:** `defense.get("DB", []) or defense.get("LB", [])` — does `_pick()` handle an all-zero-weight list gracefully, or does it need a guard? Architect should verify and add a guard if needed.
2. **`rusher` in scope at TURNOVER_FUMBLE branch:** `secondary_player_id = rusher.player_id` requires `rusher` to be defined before the fumble branch. Architect should confirm variable scope in the existing `resolve_play()` flow.
3. **Alembic FK convention:** Existing migrations may use inline `ForeignKey()` in `add_column` or separate `create_foreign_key`. Architect should check existing `alembic/versions/` files and match the pattern.

---

## Handoff

**Next role:** architect

Architect reads this file plus `roles/brief/output/output.md`. Key work:
- Confirm `PlayOutcome.__slots__` and `__init__` extension
- Confirm `game.py` INSERT pattern (raw dict, named params, or ORM)
- Read existing alembic migrations and match FK convention
- Resolve the 3 open questions above
- Produce exact code snippets the implementer can drop in
