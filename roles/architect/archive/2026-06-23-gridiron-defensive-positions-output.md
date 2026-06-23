# Architect Output — gridiron: Defensive Position Expansion + Pass Rush Pre-Picks

**Role:** architect
**Sequence:** add-feature
**Date:** 2026-06-23

---

## Open Questions Resolved

**Q1 — `_pick()` on DB group with no `DB`-coded players:**
After migration `CB` remains `CB` and enters the `"DB": ["CB", "DB"]` group. `defense.get("DB")` will return the CB-populated slot list — not empty. The only 0-player sub-code is `"DB"` (nickel/slot), but those are mixed into the same group bucket. `_pick()` returns None only if the whole group list is empty. Safe.

**Q2 — SACK fallback when `dl_rusher` is None:**
`sacker = dl_rusher or lb_rusher`. Python short-circuits to `lb_rusher` when DL pool is empty. `dl_player_id` set from `dl_rusher` (None if empty), `lb_player_id` set from `lb_rusher` (always). `primary_player_id` = `sacker`.

**Q3 — ROLB starters=2 acceptable:**
`build_roster_map` takes top-3 by score. With 2 starters + 1 reserve, all 3 ROLB enter the roster map with snap weights `[0.65, 0.225, 0.125]`. No issue.

---

## System Overview

Six additive/update changes across four files. Alembic migration (1) splits existing player position codes and adds `s_player_id` column to `play_log`. `seed_roster.py` (2) gets new `POSITION_DISTRIBUTION` and `JERSEY_RANGES`. `constants.py` (3) updates `POSITION_GROUPS` to address `LB`, `DB`, and `S` independently. `play_resolver.py` (4) adds `s_player_id` to `PlayOutcome`, adds `lb_rusher` + `s_coverage` pre-picks to the PASS block, and threads them through all pass return sites. `game.py` (5) extends `_to_row()` and the INSERT SQL. No structural changes — all additive.

---

## Data Models

### `PlayOutcome` — one new slot

Current `__slots__` already has 16 entries. Add `s_player_id` as the 17th:

```python
__slots__ = (
    "play_type", "yards", "primary_player_id", "description",
    "x", "y", "possession_score_delta", "defending_score_delta",
    "possession_changes", "next_field_pos", "td_type",
    "secondary_player_id", "tackler_player_id",
    "ol_player_id", "dl_player_id", "lb_player_id",
    "s_player_id",   # ← new
)
```

`__init__` signature: add `s_player_id: int | None = None` after `lb_player_id`.
`__init__` body: add `self.s_player_id = s_player_id`.

All existing `PlayOutcome(...)` call sites default to `None` — no breakage.

---

## Module Interfaces

### 1. Alembic migration — new file

**Revision ID:** `b8c9d0e1f2a3`  
**Down-revision:** `a7b8c9d0e1f2` (current head)

```python
"""defensive_position_expansion

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-06-23

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b8c9d0e1f2a3"
down_revision: str | None = "a7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Split OLB → LOLB (even id) / ROLB (odd id)
    op.execute("UPDATE players SET position='LOLB' WHERE position='OLB' AND id % 2 = 0")
    op.execute("UPDATE players SET position='ROLB' WHERE position='OLB' AND id % 2 = 1")
    # Split S → SS (even id) / FS (odd id)
    op.execute("UPDATE players SET position='SS' WHERE position='S' AND id % 2 = 0")
    op.execute("UPDATE players SET position='FS' WHERE position='S' AND id % 2 = 1")
    # Add s_player_id column
    op.add_column(
        "play_log",
        sa.Column("s_player_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("play_log", "s_player_id")
    op.execute("UPDATE players SET position='S' WHERE position IN ('SS', 'FS')")
    op.execute("UPDATE players SET position='OLB' WHERE position IN ('LOLB', 'ROLB')")
```

### 2. `scripts/seed_roster.py` — POSITION_DISTRIBUTION + JERSEY_RANGES

Replace `POSITION_DISTRIBUTION` (lines 30–61):

```python
POSITION_DISTRIBUTION: list[tuple[str, int]] = [
    ("QB", 3),
    ("RB", 4),
    ("FB", 2),
    ("WR", 8),
    ("TE", 4),
    ("LT", 3),
    ("LG", 3),
    ("C", 3),
    ("RG", 3),
    ("RT", 3),
    ("DE", 5),
    ("DT", 5),
    ("LOLB", 3),
    ("MLB", 4),
    ("ROLB", 2),
    ("CB", 6),
    ("DB", 1),
    ("SS", 3),
    ("FS", 2),
    ("K", 1),
    ("P", 2),
    ("LS", 1),
    ("ATH", 4),
    # Reserve/Walk-on (10 total)
    ("QB", 1),
    ("RB", 1),
    ("WR", 2),
    ("ROLB", 1),
    ("CB", 1),
    ("DE", 1),
    ("LT", 1),
    ("FS", 1),
    ("ATH", 1),
]
```

Total check: starters 3+4+2+8+4+3+3+3+3+3+5+5+3+4+2+6+1+3+2+1+2+1+4 = 75; reserves 1+1+2+1+1+1+1+1+1 = 10; total = 85 ✓

Replace `JERSEY_RANGES` (lines 71–92):

```python
JERSEY_RANGES: dict[str, tuple[int, int]] = {
    "QB":   (1, 19),
    "RB":   (20, 39),
    "FB":   (20, 49),
    "WR":   (1, 19),
    "TE":   (40, 89),
    "LT":   (50, 79),
    "LG":   (50, 79),
    "C":    (50, 79),
    "RG":   (50, 79),
    "RT":   (50, 79),
    "DE":   (90, 99),
    "DT":   (90, 99),
    "LOLB": (40, 59),
    "ROLB": (40, 59),
    "MLB":  (40, 59),
    "CB":   (20, 49),
    "DB":   (20, 49),
    "SS":   (20, 49),
    "FS":   (20, 49),
    "K":    (1, 19),
    "P":    (1, 19),
    "LS":   (50, 79),
    "ATH":  (1, 49),
}
```

### 3. `gridiron/engine/constants.py` — POSITION_GROUPS (gitignored)

Change:
```python
"LB": ["OLB", "MLB"],
"DB": ["CB", "S"],
```
To:
```python
"LB": ["LOLB", "MLB", "ROLB"],
"DB": ["CB", "DB"],
"S":  ["SS", "FS"],
```

### 4. `gridiron/engine/play_resolver.py` — PASS block (gitignored)

**Step A — extend `PlayOutcome`** (lines 31–73): add slot + init param + assignment as described in Data Models above.

**Step B — PASS block pre-picks** (current lines 222–223):

Existing:
```python
ol_blocker = _pick(offense.get("OL", []))
dl_rusher  = _pick(defense.get("DL", []))
```
Replace with:
```python
ol_blocker = _pick(offense.get("OL", []))
dl_rusher  = _pick(defense.get("DL", []))
lb_rusher  = _pick(defense.get("LB", []))
s_coverage = _pick(defense.get("S", []))
```

**Step C — SACK return** (current lines 239–250):

Replace the `def_slot` pick with the pre-picked players:
```python
if roll < sack_prob:
    sacker = dl_rusher or lb_rusher
    d_name = sacker.last_name if sacker else "defender"
    sack_yards = random.randint(-10, -4)
    return PlayOutcome(
        "SACK", sack_yards, sacker.player_id if sacker else None,
        _desc("SACK", d_name, sack_yards),
        max(1, state.field_position + sack_yards), 27,
        secondary_player_id=qb.player_id if qb else None,
        ol_player_id=ol_blocker.player_id if ol_blocker else None,
        dl_player_id=dl_rusher.player_id if dl_rusher else None,
        lb_player_id=lb_rusher.player_id if lb_rusher else None,
    )
```

**Step D — TURNOVER_INTERCEPTION** (current lines 251–264): add `lb_player_id` + `s_player_id`:

```python
if roll < sack_prob + int_prob:
    def_slot = _pick(defense.get("DB", []) or defense.get("S", []))
    d_name = def_slot.last_name if def_slot else "defender"
    return PlayOutcome(
        "TURNOVER_INTERCEPTION", 0,
        def_slot.player_id if def_slot else None,
        _desc("TURNOVER_INTERCEPTION", d_name),
        state.field_position, 27,
        possession_changes=True,
        next_field_pos=max(5, 100 - state.field_position),
        secondary_player_id=qb.player_id if qb else None,
        ol_player_id=ol_blocker.player_id if ol_blocker else None,
        dl_player_id=dl_rusher.player_id if dl_rusher else None,
        lb_player_id=lb_rusher.player_id if lb_rusher else None,
        s_player_id=s_coverage.player_id if s_coverage else None,
    )
```

Note: interceptor primary pick expands to `DB or S` — corners/nickel intercept, but safeties do too.

**Step E — PASS_COMPLETE** (current lines 265–278): add `lb_player_id` + `s_player_id`:

```python
if roll < sack_prob + int_prob + complete_prob:
    yards_std = PASS_YARDS_STD * (1.0 - sigma * 0.3)
    yards = max(1, round(random.gauss(PASS_YARDS_MEAN + elo_yards, yards_std)))
    db_closer = _pick(defense.get("DB", []) or defense.get("S", []))
    return PlayOutcome(
        "PASS_COMPLETE", yards,
        receiver.player_id if receiver else None,
        _desc("PASS_COMPLETE", r_name, yards),
        state.field_position + yards, 27,
        secondary_player_id=qb.player_id if qb else None,
        tackler_player_id=db_closer.player_id if db_closer else None,
        ol_player_id=ol_blocker.player_id if ol_blocker else None,
        dl_player_id=dl_rusher.player_id if dl_rusher else None,
        lb_player_id=lb_rusher.player_id if lb_rusher else None,
        s_player_id=s_coverage.player_id if s_coverage else None,
    )
```

Note: `db_closer` expands to `DB or S` so safeties can make the tackle on completions.

**Step F — PASS_DEFLECTION** (current lines 279–289): add `lb_player_id` + `s_player_id`:

```python
if roll < sack_prob + int_prob + complete_prob + defl_prob:
    def_slot = _pick(defense.get("DB", []) or defense.get("DL", []))
    d_name = def_slot.last_name if def_slot else "defender"
    return PlayOutcome(
        "PASS_DEFLECTION", 0, def_slot.player_id if def_slot else None,
        _desc("PASS_DEFLECTION", d_name),
        state.field_position, 27,
        secondary_player_id=qb.player_id if qb else None,
        ol_player_id=ol_blocker.player_id if ol_blocker else None,
        dl_player_id=dl_rusher.player_id if dl_rusher else None,
        lb_player_id=lb_rusher.player_id if lb_rusher else None,
        s_player_id=s_coverage.player_id if s_coverage else None,
    )
```

**Step G — PASS_INCOMPLETE** (current lines 290–299): add `lb_player_id` + `s_player_id`:

```python
return PlayOutcome(
    "PASS_INCOMPLETE", 0,
    receiver.player_id if receiver else None,
    _desc("PASS_INCOMPLETE", r_name),
    state.field_position, 27,
    secondary_player_id=qb.player_id if qb else None,
    ol_player_id=ol_blocker.player_id if ol_blocker else None,
    dl_player_id=dl_rusher.player_id if dl_rusher else None,
    lb_player_id=lb_rusher.player_id if lb_rusher else None,
    s_player_id=s_coverage.player_id if s_coverage else None,
)
```

### 5. `gridiron/engine/game.py` — `_to_row()` + INSERT (gitignored)

**`_to_row()` dict** (current line 576–580): add after `lb_player_id`:
```python
"s_player_id":         outcome.s_player_id,
```

**INSERT SQL** (current lines 401–411): add `s_player_id` to both columns and values lists:
```python
"INSERT INTO play_log "
"(game_id, play_number, quarter, possession, play_type, "
"yards_gained, field_pos_before, field_pos_after, "
"score_home, score_away, primary_player_id, description, x_coord, y_coord, "
"down, distance, "
"secondary_player_id, tackler_player_id, ol_player_id, dl_player_id, lb_player_id, s_player_id) "
"VALUES (:game_id, :play_number, :quarter, :possession, :play_type, "
":yards_gained, :field_pos_before, :field_pos_after, "
":score_home, :score_away, :primary_player_id, :description, :x_coord, :y_coord, "
":down, :distance, "
":secondary_player_id, :tackler_player_id, :ol_player_id, :dl_player_id, :lb_player_id, :s_player_id)"
```

---

## Dependencies

```
alembic migration (b8c9d0e1f2a3)
  └── depends on: players.position column, play_log table, a7b8c9d0e1f2 head

scripts/seed_roster.py
  └── standalone; no engine dep. Affects future re-seeds only.

constants.py (gitignored)
  └── consumed by build_roster_map() in game.py

play_resolver.py (gitignored)
  └── depends on: POSITION_GROUPS via constants, PlayOutcome shape

game.py (gitignored)
  └── depends on: PlayOutcome.s_player_id, play_log schema (s_player_id column)
```

Apply order: migration → constants.py → play_resolver.py → game.py. seed_roster.py is independent.

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Existing RUSH `lb_player_id` | RUSH block pre-picks `lb_defender = _pick(defense.get("LB", []))`. After the migration, LB group = LOLB+MLB+ROLB. RUSH attribution is unchanged — `lb_player_id` already populated on RUSH. No action needed. |
| SACK `def_slot` removal | Current SACK code picks `def_slot = _pick(defense.get("DL", []) or defense.get("LB", []))` separately. Sprint B eliminates this pick — SACK now uses the pre-picked `dl_rusher` and `lb_rusher`. Remove the `def_slot` pick line entirely inside the SACK branch. |
| `_pick()` on empty S group | If a game runs before migration (old position codes), `defense.get("S", [])` = empty → `s_coverage = None` → `s_player_id = None`. Safe. |
| ruff | `seed_roster.py` is tracked. Run `ruff check --fix scripts/seed_roster.py` after changes. |
| Only one INSERT site | Confirmed: single `self.conn.execute(text("INSERT INTO play_log ..."))` at ~line 399. OT drive appends to the same `plays` list — no second INSERT to update. |

---

## Implementation Notes for Implementer

1. **Migration first.** `uv run alembic upgrade head` must succeed before running engine or you'll get `column s_player_id does not exist`.

2. **Verify position split after migration:**
   ```sql
   SELECT position, COUNT(*) FROM players GROUP BY position ORDER BY position;
   ```
   Expected: no OLB or S rows. LOLB, ROLB, SS, FS all present.

3. **SACK branch:** Delete the old `def_slot = _pick(defense.get("DL", []) or defense.get("LB", []))` line inside the SACK branch. Replace references to `def_slot` with `sacker` as specified above.

4. **TURNOVER_INTERCEPTION interceptor pick:** Change `_pick(defense.get("DB", []))` to `_pick(defense.get("DB", []) or defense.get("S", []))` so safeties can intercept. Primary player ID = the interceptor (correct).

5. **Verification query after one game run:**
   ```sql
   SELECT play_type,
          COUNT(*) AS plays,
          COUNT(lb_player_id) AS has_lb,
          COUNT(s_player_id) AS has_s
   FROM play_log
   WHERE game_id = (SELECT MAX(id) FROM games WHERE status='complete')
   GROUP BY play_type ORDER BY play_type;
   ```
   Expected: PASS_COMPLETE rows all have `has_lb > 0` and `has_s > 0`. RUSH rows have `has_lb > 0`, `has_s = 0`.

---

## Handoff

**Next role:** implementer

Execute in order:
1. Create `alembic/versions/b8c9d0e1f2a3_defensive_position_expansion.py` — run `uv run alembic upgrade head`
2. Edit `scripts/seed_roster.py` — `POSITION_DISTRIBUTION` + `JERSEY_RANGES` — run `ruff check --fix`
3. Edit `gridiron/engine/constants.py` — `POSITION_GROUPS` keys
4. Edit `gridiron/engine/play_resolver.py` — `PlayOutcome` slot, PASS pre-picks, 5 return sites
5. Edit `gridiron/engine/game.py` — `_to_row()` + INSERT SQL
6. Trigger one game, run verification query
7. Commit tracked files: migration + seed_roster.py (engine files are gitignored — not committed)
