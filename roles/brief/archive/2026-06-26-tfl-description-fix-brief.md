# Brief: tfl-description-fix

**Role:** brief
**Sprint unit:** 01
**Project:** gridiron
**Date:** 2026-06-26

---

## Context

In `play_resolver.py`, the TACKLE_FOR_LOSS outcome description is built using `r_name` (the rusher's last name) as the `{player}` slot in the description template. TFL descriptions should credit the **tackler** (the defender who stopped the play), not the ball carrier. The variable `tackler` (= `dl_defender or lb_defender`) is already computed at line 219 but its name is never used in the description.

---

## Objective

Fix `_desc("TACKLE_FOR_LOSS", ...)` to pass the tackler's name instead of the rusher's name.

---

## Specification

**File:** `gridiron/engine/play_resolver.py` (gitignored)

### File map

| Symbol | File | Approx line |
|---|---|---|
| `r_name` assignment | `gridiron/engine/play_resolver.py` | 199 |
| `tackler` assignment | `gridiron/engine/play_resolver.py` | 219 |
| TFL `PlayOutcome` return | `gridiron/engine/play_resolver.py` | 240–248 |
| `_desc` function | `gridiron/engine/play_resolver.py` | 85 |

### Change

In the `if yards < 0:` branch (TFL), before the `return PlayOutcome(...)`:

Add:
```python
t_name = tackler.last_name if tackler else "defender"
```

Then change:
```python
_desc("TACKLE_FOR_LOSS", r_name, yards),
```
to:
```python
_desc("TACKLE_FOR_LOSS", t_name, yards),
```

`r_name` is still needed for other play outcomes in this block — do not remove it.

---

## Out of Scope

- Do not change `primary_player_id` on TFL (stays as rusher — that's correct for stats attribution)
- Do not change `accumulate_stats` in `game.py` — TFL stats fix is in unit 03
- Do not touch any tracked files

---

## Verification

After the change, run a game and check the play-by-play descriptions. TFL descriptions should name a DL or LB player, not the running back.

```bash
# Run the sim sandbox to generate plays
uv run python scripts/sim_sandbox.py

# Check TFL descriptions in play_log
uv run python3 -c "
import asyncio
from gridiron.database import engine
from sqlalchemy import text

async def main():
    async with engine.begin() as conn:
        r = await conn.execute(text('''
            SELECT play_type, description
            FROM play_log WHERE play_type = 'TACKLE_FOR_LOSS'
            ORDER BY id DESC LIMIT 5
        '''))
        for row in r.mappings():
            print(dict(row))

asyncio.run(main())
"
```

Expected: description names a defensive player (e.g. "Williams stops the run for -3 yards"), not the ball carrier.

---

## Handoff

Commit message: `fix: TFL description credits tackler not ball carrier`
Next unit: 02 (h2h-tiebreaker) — no dependency on this unit.
