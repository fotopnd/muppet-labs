# Implementer Output — gridiron: play_log Multi-Player Attribution

**Role:** implementer
**Sequence:** add-feature
**Date:** 2026-06-23

---

## Phase

Single-language — Python only. No frontend changes in scope.

---

## Files Produced

| File | Purpose |
|------|---------|
| `alembic/versions/a7b8c9d0e1f2_play_log_attribution.py` | Migration: 5 nullable FK columns added to `play_log` |
| `gridiron/engine/constants.py` | Added `"OL": ["LT", "LG", "C", "RG", "RT"]` to `POSITION_GROUPS` |
| `gridiron/engine/play_resolver.py` | `PlayOutcome` slots + init + 7 return sites updated (gitignored) |
| `gridiron/engine/game.py` | `_to_row()` + INSERT SQL extended with 5 new columns (gitignored) |

---

## Setup Steps Taken

None — project already initialised.

---

## Verification

```
uv run alembic upgrade head
→ Running upgrade f6a7b8c9d0e1 -> a7b8c9d0e1f2, play_log_attribution

uv run ruff check --fix + ruff format  (constants.py + migration)
→ 7 fixed, 0 remaining. 2 files reformatted.

Game 1308 re-run, new columns sampled:
```

| play_type | secondary | tackler | ol | dl | lb |
|---|---|---|---|---|---|
| RUSH | ✅ False | ✅ True | ✅ True | ✅ True | ✅ True |
| TACKLE_FOR_LOSS | ✅ False | ✅ True | ✅ True | ✅ True | ✅ True |
| TURNOVER_FUMBLE | ✅ True (rusher) | ✅ True (recoverer) | ✅ True | ✅ True | ✅ True |
| PASS_COMPLETE | ✅ True (QB) | ✅ True (DB closer) | ✅ True | ✅ True | ✅ False |
| PASS_INCOMPLETE | ✅ True (QB) | ✅ False | ✅ True | ✅ True | ✅ False |
| PASS_DEFLECTION | ✅ True (QB) | ✅ False | ✅ True | ✅ True | ✅ False |
| SACK | ✅ True (QB) | ✅ False | ✅ True (missed block) | ✅ True (=primary) | ✅ False |
| TURNOVER_INTERCEPTION | ✅ True (QB) | ✅ False | ✅ True | ✅ True | ✅ False |
| FIELD_GOAL, PAT, PUNT, TOUCHDOWN | ✅ all NULL (expected) | | | | |

All 6 success criteria from the brief are met.

---

## Deviations from Architecture

None. Implementation matches architect spec exactly.

---

## Known Gaps

- TOUCHDOWN rows (created inline in `game.py` after RUSH/PASS_COMPLETE reaches goal line) have NULL in all 5 new columns. Expected per architect notes — these bypass `resolve_play()`. Documented in architect output.
- PAT, FG, PUNT rows: all NULL. Expected — special teams out of scope.
- `player_game_stats` not extended — aggregation deferred to follow-up sprint.
- No `RUSH_TD` or `PASS_TD` play type exists in the engine — TD outcome is a separate `TOUCHDOWN` row, not a subtype of RUSH/PASS. Field-assignment table for those entries in the planner output is moot.

---

## How to Run

```bash
# Verify schema
uv run python3 -c "
import asyncio
from gridiron.database import engine
from sqlalchemy import text
async def main():
    async with engine.begin() as conn:
        r = await conn.execute(text('''
            SELECT play_type,
                   secondary_player_id IS NOT NULL AS has_secondary,
                   ol_player_id IS NOT NULL AS has_ol,
                   dl_player_id IS NOT NULL AS has_dl,
                   lb_player_id IS NOT NULL AS has_lb
            FROM play_log WHERE game_id = (SELECT MAX(id) FROM games WHERE status = 'complete')
            GROUP BY play_type, has_secondary, has_ol, has_dl, has_lb
            ORDER BY play_type
        '''))
        for row in r.mappings(): print(dict(row))
asyncio.run(main())
"
```

---

## Handoff

Next role: reviewer.

Reviewer should:
1. Confirm `POSITION_GROUPS` change activates OL players via `build_roster_map` (verify OL slots are non-empty in a game roster)
2. Check that `_pick()` is called on `offense.get("OL", [])` — if no OL players loaded, all `ol_player_id` would be NULL even on RUSH plays
3. Confirm the SACK intentional redundancy (`dl_player_id = primary_player_id`) is the right call — could be dropped if query writers prefer the UNION approach
4. Verify the migration `downgrade()` is correct (reverse order)
5. Confirm ruff passes on both tracked files
