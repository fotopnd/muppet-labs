# Brief: player-stats-extension

**Role:** brief
**Sprint unit:** 03
**Project:** gridiron
**Date:** 2026-06-26
**Depends on:** unit 01 (tfl-description-fix) — unit 01 must be merged before this runs

---

## Context

`player_game_stats` has a stats accuracy bug and two missing stat columns:

1. **TFL tackle credit bug:** `accumulate_stats` (game.py line 185-186) credits `outcome.primary_player_id` with `tackles=1` on TACKLE_FOR_LOSS. `primary_player_id` on a TFL is the *rusher* — the ball carrier being stopped — not the tackler. The correct recipient is `outcome.tackler_player_id`.

2. **Missing DL pressures:** `dl_player_id` is populated on every pass play (SACK, PASS_COMPLETE, PASS_INCOMPLETE, PASS_DEFLECTION, TURNOVER_INTERCEPTION) via the attribution columns added in the play_log attribution sprint. These DL pass rush events are never aggregated into `player_game_stats`.

3. **Missing LB tackles:** `lb_player_id` is populated on every RUSH and TFL play. These are never aggregated.

---

## Objective

- Fix the TFL tackles stat bug (credit defender, not ball carrier)
- Add `dl_pressures` and `lb_tackles` to `player_game_stats` via migration
- Populate both in `accumulate_stats`
- Expose in `PlayerGameStats` schema

---

## Specification

### 1. Alembic migration

New file: `alembic/versions/<new_rev>_player_stats_dl_lb.py`
- `down_revision = 'c9d0e1f2a3b4'` (current head)
- New revision ID: pick a fresh 12-char hex, e.g. `d5e6f7a8b9c0`

```python
def upgrade() -> None:
    op.add_column("player_game_stats", sa.Column("dl_pressures", sa.Integer(), server_default="0", nullable=False))
    op.add_column("player_game_stats", sa.Column("lb_tackles", sa.Integer(), server_default="0", nullable=False))

def downgrade() -> None:
    op.drop_column("player_game_stats", "lb_tackles")
    op.drop_column("player_game_stats", "dl_pressures")
```

Run: `uv run alembic upgrade head`

### 2. `gridiron/engine/game.py` — fix `accumulate_stats` (gitignored)

**File map:**

| Symbol | File | Approx line |
|---|---|---|
| `accumulate_stats` function | `gridiron/engine/game.py` | 151 |
| `_credit` helper | `gridiron/engine/game.py` | ~140 |
| RUSH branch | `gridiron/engine/game.py` | 161–162 |
| TACKLE_FOR_LOSS branch | `gridiron/engine/game.py` | 185–186 |
| SACK branch | `gridiron/engine/game.py` | 183–184 |
| PASS_COMPLETE branch | `gridiron/engine/game.py` | 170–175 |
| PASS_INCOMPLETE branch | `gridiron/engine/game.py` | 176–178 |
| PASS_DEFLECTION branch | `gridiron/engine/game.py` | 180–182 |
| TURNOVER_INTERCEPTION branch | `gridiron/engine/game.py` | 187–190 |
| `write_stats` INSERT | `gridiron/engine/game.py` | 210–220 |

**Changes to `accumulate_stats`:**

a) Fix TFL — change:
```python
elif outcome.play_type == "TACKLE_FOR_LOSS":
    _credit(stats, pid, tackles=1)
```
to:
```python
elif outcome.play_type == "TACKLE_FOR_LOSS":
    _credit(stats, outcome.tackler_player_id, tackles=1)
    _credit(stats, outcome.lb_player_id, lb_tackles=1)
```

b) Add LB tackle credit on RUSH — change:
```python
if outcome.play_type == "RUSH":
    _credit(stats, pid, rush_attempts=1, rush_yards=y)
```
to:
```python
if outcome.play_type == "RUSH":
    _credit(stats, pid, rush_attempts=1, rush_yards=y)
    _credit(stats, outcome.lb_player_id, lb_tackles=1)
```

c) Add DL pressure credits — after each existing credit in SACK, PASS_COMPLETE, PASS_INCOMPLETE, PASS_DEFLECTION, TURNOVER_INTERCEPTION branches, add:
```python
_credit(stats, outcome.dl_player_id, dl_pressures=1)
```

Specifically:
- SACK (line ~183): add `_credit(stats, outcome.dl_player_id, dl_pressures=1)` after existing `_credit(stats, pid, sacks=1)`
- PASS_COMPLETE (line ~170-175): add after receiver credit
- PASS_INCOMPLETE (line ~176-178): add after qb attempt credit
- PASS_DEFLECTION (line ~180-182): add after qb attempt credit
- TURNOVER_INTERCEPTION (line ~187-190): add after ints_def credit

**Changes to `write_stats` INSERT:**

In `write_stats` (line ~210), add `dl_pressures` and `lb_tackles` to:
- the column list in the INSERT string
- the VALUES placeholder string
- the default dict (ensure `_credit` initialises them — check the `_credit` helper initialisation pattern and add `dl_pressures=0, lb_tackles=0` to the default stat dict if needed)

Check the `_credit` function and the default stats dict initialisation to see where zero-defaults are set; add the two new keys there.

### 3. `gridiron/api/schemas.py` — add new fields to `PlayerGameStats`

Add to `PlayerGameStats` (currently ends around line 127):
```python
dl_pressures: int = 0
lb_tackles: int = 0
```

---

## Out of Scope

- Do not add OL blocks stat — on-every-play volume makes it meaningless without a filter
- Do not change the leaderboard or programs stats SQL queries — they SELECT all columns from `player_game_stats` via the schema; Pydantic will handle the new fields via `model_validate`
- Do not change `play_resolver.py` — unit 01 owns that file

---

## Verification

```bash
# 1. Migration
uv run alembic upgrade head

# 2. Run a game
uv run python scripts/sim_sandbox.py

# 3. Check new stats populated
uv run python3 -c "
import asyncio
from gridiron.database import engine
from sqlalchemy import text

async def main():
    async with engine.begin() as conn:
        # DL pressures
        r = await conn.execute(text('''
            SELECT pl.last_name, pl.position, SUM(pgs.dl_pressures) AS pressures
            FROM player_game_stats pgs JOIN players pl ON pl.id = pgs.player_id
            WHERE pgs.dl_pressures > 0
            GROUP BY pl.id, pl.last_name, pl.position
            ORDER BY pressures DESC LIMIT 5
        '''))
        print('DL pressures:', [dict(row) for row in r.mappings()])

        # LB tackles
        r = await conn.execute(text('''
            SELECT pl.last_name, pl.position, SUM(pgs.lb_tackles) AS tackles
            FROM player_game_stats pgs JOIN players pl ON pl.id = pgs.player_id
            WHERE pgs.lb_tackles > 0
            GROUP BY pl.id, pl.last_name, pl.position
            ORDER BY tackles DESC LIMIT 5
        '''))
        print('LB tackles:', [dict(row) for row in r.mappings()])

        # TFL tackles sanity: no RB/WR/QB should have tackles
        r = await conn.execute(text('''
            SELECT pl.position, SUM(pgs.tackles) AS tackles
            FROM player_game_stats pgs JOIN players pl ON pl.id = pgs.player_id
            WHERE pgs.tackles > 0
            GROUP BY pl.position ORDER BY tackles DESC
        '''))
        print('Tackles by position (should be DL/LB only):', [dict(row) for row in r.mappings()])

asyncio.run(main())
"

# 4. Check API schema exposes new fields
curl http://localhost:8006/programs/1/roster | python3 -m json.tool | grep -E "dl_pressures|lb_tackles" | head -5
```

Expected:
- DL pressures appear for DL-position players only
- LB tackles appear for LB-position players only
- `tackles` column in player_game_stats now credits DL/LB positions, not RB/WR

---

## Handoff

Commit message: `fix: player_game_stats TFL tackles + DL pressures + LB tackles`
After this unit: combined reviewer pass, then retro.
