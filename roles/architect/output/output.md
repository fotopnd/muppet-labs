# Architect Output — gridiron: play_log Multi-Player Attribution

**Role:** architect
**Sequence:** add-feature
**Date:** 2026-06-23

---

## Open Questions Resolved

**Q1 — `_pick()` on empty-weight list:** `_pick` already guards `if not slots: return None`. `random.choices` with all-zero weights would raise `ValueError` in theory, but `snap_weight = sigma*0.4 + alpha*0.3 + psi*0.3` with 0–1 attributes makes all-zero weights impossible in practice. No guard needed.

**Q2 — `rusher` in scope at TURNOVER_FUMBLE branch:** Confirmed. `rusher = _pick(...)` at line 148; fumble branch at lines 164–174. `rusher` is in scope. `secondary_player_id = rusher.player_id if rusher else None` is safe.

**Q3 — Alembic FK convention:** Existing `create_table` uses inline `sa.ForeignKey('players.id')` inside `sa.Column()`. Existing `add_column` calls (`e5f6a7b8c9d0`, `f6a7b8c9d0e1`) don't add FK columns. For the new migration, use inline `sa.ForeignKey('players.id')` in `op.add_column` — this is the correct pattern and matches how `primary_player_id` was originally defined.

---

## System Overview

Four additive changes, no structural rewrites. `constants.py` gets one new dict key. A new Alembic migration adds 5 nullable FK columns to `play_log`. `PlayOutcome` in `play_resolver.py` gets 5 new optional slots. `play_resolver.py` pre-picks OL/DL/LB players once per play category and passes them through to each `PlayOutcome` constructor. `game.py`'s `_to_row()` dict and the bulk INSERT SQL gain the 5 new keys. All gitignored engine files are disk-only.

---

## Data Models

### `PlayOutcome` — extended `__slots__` and `__init__`

```python
class PlayOutcome:
    __slots__ = (
        "play_type", "yards", "primary_player_id", "description",
        "x", "y", "possession_score_delta", "defending_score_delta",
        "possession_changes", "next_field_pos", "td_type",
        # new
        "secondary_player_id", "tackler_player_id",
        "ol_player_id", "dl_player_id", "lb_player_id",
    )

    def __init__(
        self,
        play_type: str,
        yards: int,
        primary_player_id: int | None,
        description: str,
        x: int,
        y: int,
        possession_score_delta: int = 0,
        defending_score_delta: int = 0,
        possession_changes: bool = False,
        next_field_pos: int | None = None,
        td_type: str | None = None,
        # new — all keyword-only, default None
        secondary_player_id: int | None = None,
        tackler_player_id: int | None = None,
        ol_player_id: int | None = None,
        dl_player_id: int | None = None,
        lb_player_id: int | None = None,
    ) -> None:
        # ... existing assignments ...
        self.secondary_player_id = secondary_player_id
        self.tackler_player_id = tackler_player_id
        self.ol_player_id = ol_player_id
        self.dl_player_id = dl_player_id
        self.lb_player_id = lb_player_id
```

All 5 new params are keyword-only with `None` defaults — no existing `PlayOutcome(...)` call site breaks.

---

## Module Interfaces

### 1. `gridiron/engine/constants.py` — one line change

In `POSITION_GROUPS`, after `"DB": ["CB", "S"]`, add:

```python
"OL": ["LT", "LG", "C", "RG", "RT"],
```

### 2. Alembic migration — `a7b8c9d0e1f2_play_log_attribution.py`

```python
"""play_log_attribution

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-23

"""
from __future__ import annotations
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for col in [
        "secondary_player_id",
        "tackler_player_id",
        "ol_player_id",
        "dl_player_id",
        "lb_player_id",
    ]:
        op.add_column(
            "play_log",
            sa.Column(col, sa.Integer(), sa.ForeignKey("players.id"), nullable=True),
        )


def downgrade() -> None:
    for col in [
        "lb_player_id", "dl_player_id", "ol_player_id",
        "tackler_player_id", "secondary_player_id",
    ]:
        op.drop_column("play_log", col)
```

### 3. `play_resolver.py` — RUSH block additions

Insert after `yards = round(random.gauss(...))` and before the fumble check:

```python
# attribution picks — shared across all RUSH outcomes
ol_blocker  = _pick(offense.get("OL", []))
dl_defender = _pick(defense.get("DL", []))
lb_defender = _pick(defense.get("LB", []))
tackler     = dl_defender or lb_defender
```

Updated return statements (keyword args added, positional args unchanged):

**TURNOVER_FUMBLE** (existing `def_slot` = fumble recoverer, overrides pre-picked tackler):
```python
return PlayOutcome(
    "TURNOVER_FUMBLE", min(yards, 0),
    def_slot.player_id if def_slot else None,
    _desc("TURNOVER_FUMBLE", d_name),
    state.field_position, 27,
    possession_changes=True,
    next_field_pos=max(5, 100 - state.field_position),
    secondary_player_id=rusher.player_id if rusher else None,
    tackler_player_id=def_slot.player_id if def_slot else None,
    ol_player_id=ol_blocker.player_id if ol_blocker else None,
    dl_player_id=dl_defender.player_id if dl_defender else None,
    lb_player_id=lb_defender.player_id if lb_defender else None,
)
```

**TACKLE_FOR_LOSS:**
```python
return PlayOutcome(
    "TACKLE_FOR_LOSS", yards, rusher.player_id if rusher else None,
    _desc("TACKLE_FOR_LOSS", r_name, yards),
    max(1, state.field_position + yards), 27,
    tackler_player_id=tackler.player_id if tackler else None,
    ol_player_id=ol_blocker.player_id if ol_blocker else None,
    dl_player_id=dl_defender.player_id if dl_defender else None,
    lb_player_id=lb_defender.player_id if lb_defender else None,
)
```

**RUSH:**
```python
return PlayOutcome(
    "RUSH", yards, rusher.player_id if rusher else None,
    _desc("RUSH", r_name, yards),
    state.field_position + yards, 27,
    tackler_player_id=tackler.player_id if tackler else None,
    ol_player_id=ol_blocker.player_id if ol_blocker else None,
    dl_player_id=dl_defender.player_id if dl_defender else None,
    lb_player_id=lb_defender.player_id if lb_defender else None,
)
```

### 4. `play_resolver.py` — PASS block additions

Insert after `receiver = _pick(offense.get("WR", []))`:

```python
# attribution picks — shared across all PASS outcomes
ol_blocker = _pick(offense.get("OL", []))
dl_rusher  = _pick(defense.get("DL", []))
```

Updated return statements:

**SACK** (`def_slot.player_id` = sacker = primary; `dl_player_id` mirrors primary intentionally):
```python
return PlayOutcome(
    "SACK", sack_yards, def_slot.player_id if def_slot else None,
    _desc("SACK", d_name, sack_yards),
    max(1, state.field_position + sack_yards), 27,
    secondary_player_id=qb.player_id if qb else None,
    ol_player_id=ol_blocker.player_id if ol_blocker else None,
    dl_player_id=def_slot.player_id if def_slot else None,  # ponytail: dl_player_id = primary on SACK — intentional for query convenience
)
```

**TURNOVER_INTERCEPTION:**
```python
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
)
```

**PASS_COMPLETE** (new `db_closer` pick just before this return):
```python
db_closer = _pick(defense.get("DB", []) or defense.get("LB", []))
return PlayOutcome(
    "PASS_COMPLETE", yards,
    receiver.player_id if receiver else None,
    _desc("PASS_COMPLETE", r_name, yards),
    state.field_position + yards, 27,
    secondary_player_id=qb.player_id if qb else None,
    tackler_player_id=db_closer.player_id if db_closer else None,
    ol_player_id=ol_blocker.player_id if ol_blocker else None,
    dl_player_id=dl_rusher.player_id if dl_rusher else None,
)
```

**PASS_DEFLECTION:**
```python
return PlayOutcome(
    "PASS_DEFLECTION", 0, def_slot.player_id if def_slot else None,
    _desc("PASS_DEFLECTION", d_name),
    state.field_position, 27,
    secondary_player_id=qb.player_id if qb else None,
    ol_player_id=ol_blocker.player_id if ol_blocker else None,
    dl_player_id=dl_rusher.player_id if dl_rusher else None,
)
```

**PASS_INCOMPLETE:**
```python
return PlayOutcome(
    "PASS_INCOMPLETE", 0,
    receiver.player_id if receiver else None,
    _desc("PASS_INCOMPLETE", r_name),
    state.field_position, 27,
    secondary_player_id=qb.player_id if qb else None,
    ol_player_id=ol_blocker.player_id if ol_blocker else None,
    dl_player_id=dl_rusher.player_id if dl_rusher else None,
)
```

### 5. `game.py` — `_to_row()` dict extension

Add to the returned dict (after `"distance": state.distance`):

```python
"secondary_player_id": outcome.secondary_player_id,
"tackler_player_id":   outcome.tackler_player_id,
"ol_player_id":        outcome.ol_player_id,
"dl_player_id":        outcome.dl_player_id,
"lb_player_id":        outcome.lb_player_id,
```

### 6. `game.py` — INSERT SQL extension

Replace the existing INSERT SQL string with:

```python
"INSERT INTO play_log "
"(game_id, play_number, quarter, possession, play_type, "
"yards_gained, field_pos_before, field_pos_after, "
"score_home, score_away, primary_player_id, description, x_coord, y_coord, "
"down, distance, "
"secondary_player_id, tackler_player_id, ol_player_id, dl_player_id, lb_player_id) "
"VALUES (:game_id, :play_number, :quarter, :possession, :play_type, "
":yards_gained, :field_pos_before, :field_pos_after, "
":score_home, :score_away, :primary_player_id, :description, :x_coord, :y_coord, "
":down, :distance, "
":secondary_player_id, :tackler_player_id, :ol_player_id, :dl_player_id, :lb_player_id)"
```

---

## Dependencies

```
constants.py         ← POSITION_GROUPS change (tracked)
alembic migration    ← depends on: players table, play_log table (tracked)
play_resolver.py     ← depends on: PlayOutcome slots, _pick(), POSITION_GROUPS (gitignored)
game.py              ← depends on: PlayOutcome new fields, play_log schema (gitignored)
```

No circular deps. All changes are purely additive.

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Existing INSERT callers | Two INSERT sites in `game.py` (regular game loop + OT drive loop). Both call `_to_row()` — updating `_to_row()` fixes both automatically. Verify line ~401 and line ~509 grep match. |
| RUSH_TD / PASS_TD | These are `TOUCHDOWN` outcomes created inline in `game.py` after a `RUSH`/`PASS_COMPLETE` result crosses the goal line. They are separate `PlayOutcome(...)` calls, not returned from `resolve_play`. The architect notes these do NOT currently call through `resolve_play`, so they won't pick up OL/DL/LB attribution. Out of scope for this sprint — new columns stay NULL for TD rows. |
| OT drive | `_run_ot_drive()` calls `resolve_play()` and appends results via `_to_row()`. The `_to_row()` fix covers OT plays automatically — no separate change needed. |
| ruff | `constants.py` is tracked and ruff-checked. Run `ruff check` + `ruff format --check` after the constants change. Engine files are gitignored and not checked by CI. |

---

## Implementation Notes for Implementer

1. **Order of changes:** (a) migration first — `alembic upgrade head` must pass before the engine runs or you'll get `column does not exist` errors at INSERT time. (b) `constants.py` next — activates OL picks. (c) `play_resolver.py` + `game.py` last.

2. **Two INSERT sites in `game.py`:** There are two bulk INSERT calls — one in `run()` (regular game loop, around line 401) and one in `_run_ot_drive()` which feeds the same `plays` list. Both use the same SQL string. Find both occurrences and update them, OR extract the SQL to a module-level constant and update it once.

3. **`PlayOutcome` TD rows in `game.py`:** When a RUSH or PASS_COMPLETE reaches the end zone, `game.py` creates a `TOUCHDOWN` `PlayOutcome` inline (around lines 279–288 and 477–484). These bypass `resolve_play()`. Their new attribution fields will be `None` by default since the new params default to `None`. This is correct and expected.

4. **PAT plays** also bypass `resolve_play()`. Same — new fields will be `None`. Correct.

5. **Verification query** (run after one game to confirm):
```sql
SELECT play_type,
       primary_player_id IS NOT NULL AS has_primary,
       secondary_player_id IS NOT NULL AS has_secondary,
       ol_player_id IS NOT NULL AS has_ol,
       dl_player_id IS NOT NULL AS has_dl,
       lb_player_id IS NOT NULL AS has_lb
FROM play_log
WHERE game_id = (SELECT MAX(id) FROM games WHERE status = 'complete')
ORDER BY play_number;
```

---

## Handoff

**Next role:** implementer

Implementer reads this file. Execute in order:
1. Create `alembic/versions/a7b8c9d0e1f2_play_log_attribution.py` with the migration above — run `uv run alembic upgrade head`
2. Edit `gridiron/engine/constants.py` — add `"OL"` key
3. Edit `gridiron/engine/play_resolver.py` — extend `PlayOutcome`, add picks, update all 7 return sites
4. Edit `gridiron/engine/game.py` — extend `_to_row()` dict and both INSERT SQL strings
5. Run the verification query above after triggering one game
