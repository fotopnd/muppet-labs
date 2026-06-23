# Implementer Output — gridiron: Defensive Position Expansion + Pass Rush Pre-Picks

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
| `alembic/versions/b8c9d0e1f2a3_defensive_position_expansion.py` | Migration: OLB→LOLB/ROLB, S→SS/FS (player_id parity), + `s_player_id` FK column on `play_log` |
| `scripts/seed_roster.py` | Updated `POSITION_DISTRIBUTION` (LOLB/ROLB/CB/DB/SS/FS) and `JERSEY_RANGES` |
| `gridiron/engine/constants.py` | `POSITION_GROUPS`: LB=[LOLB,MLB,ROLB], DB=[CB,DB], S=[SS,FS] (gitignored) |
| `gridiron/engine/play_resolver.py` | `PlayOutcome` + `s_player_id` slot; PASS block adds `lb_rusher`/`s_coverage` pre-picks; 5 pass return sites updated (gitignored) |
| `gridiron/engine/game.py` | `_to_row()` + INSERT SQL extended with `s_player_id` (gitignored) |

---

## Setup Steps Taken

None — project already initialised.

---

## Verification

```
uv run alembic upgrade head
→ Running upgrade a7b8c9d0e1f2 -> b8c9d0e1f2a3, defensive_position_expansion

SELECT position, COUNT(*) FROM players GROUP BY position:
  LOLB=371, ROLB=409 (was OLB=780)
  SS=395, FS=385 (was S=780)
  CB=1040, MLB=520 unchanged
  No OLB or S rows remain ✓
```

Game 19 (fresh scheduled game) attribution results:

| play_type | plays | lb (%) | s (%) |
|---|---|---|---|
| PASS_COMPLETE | 38 | 38 (100%) | 38 (100%) |
| PASS_DEFLECTION | 4 | 4 (100%) | 4 (100%) |
| PASS_INCOMPLETE | 17 | 17 (100%) | 17 (100%) |
| TURNOVER_INTERCEPTION | 1 | 1 (100%) | 1 (100%) |
| SACK | 3 | 3 (100%) | 0 (0%) |
| RUSH | 35 | 35 (100%) | 0 (0%) |
| TACKLE_FOR_LOSS | 16 | 16 (100%) | 0 (0%) |
| TURNOVER_FUMBLE | 2 | 2 (100%) | 0 (0%) |
| TOUCHDOWN | 4 | 0 (0%) | 0 (0%) |
| FIELD_GOAL_ATTEMPT | 10 | 0 (0%) | 0 (0%) |
| PAT/PUNT | — | 0 (0%) | 0 (0%) |

All success criteria from planner met.

Ruff pre-existing errors: 10 E501/E731 violations in seed_roster.py are pre-existing (docstring, SQL strings, lambda in draw_attrs) — none introduced by our changes. Migration file passes clean.

---

## Deviations from Architecture

**SACK `dl_player_id` comment removed:** The architect spec noted `# ponytail: mirrors primary` for SACK's `dl_player_id`. The new SACK branch uses `dl_rusher` (which may be None if DL pool is empty) rather than `def_slot` (was always the sacker). So `dl_player_id` no longer necessarily mirrors `primary_player_id`. Comment removed as it no longer applies.

All other changes match architect spec exactly.

---

## Known Gaps

- TOUCHDOWN, PAT, PUNT, FIELD_GOAL rows: `lb_player_id` and `s_player_id` are NULL. Expected — these bypass `resolve_play()` per architect spec.
- `DB` (nickel/slot) position code: 0 players in DB post-migration. Future re-seeds will produce DB players. The DB group (`"DB": ["CB", "DB"]`) has CB players and works correctly now.
- `player_game_stats` not extended — LB pressures, S coverage grades deferred to follow-up sprint.
- Pre-existing ruff E501/E731 in seed_roster.py not fixed (not introduced by this sprint).

---

## How to Run

```bash
# Verify position migration
cd projects/gridiron
uv run python3 -c "
from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://gridiron:gridiron@localhost:5438/gridiron')
with engine.connect() as conn:
    for r in conn.execute(text('SELECT position, COUNT(*) FROM players GROUP BY position ORDER BY position')).fetchall():
        print(r[0], r[1])
"

# Verify attribution after game run
uv run python3 -c "
from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://gridiron:gridiron@localhost:5438/gridiron')
with engine.connect() as conn:
    rows = conn.execute(text('''
        SELECT play_type, COUNT(*) plays, COUNT(lb_player_id) lb, COUNT(s_player_id) s
        FROM play_log WHERE game_id=(SELECT MAX(id) FROM games WHERE status='complete')
        GROUP BY play_type ORDER BY play_type
    ''')).fetchall()
    for r in rows: print(r[0], r[1], r[2], r[3])
"
```

---

## Handoff

Next role: reviewer.

Reviewer should:
1. Confirm `POSITION_GROUPS` now has 3 separate groups for LB/DB/S — verify `defense.get("S", [])` returns SS+FS players via `build_roster_map`
2. Confirm SACK now uses pre-picked `dl_rusher or lb_rusher` (not a separate pick) — check that `d_name` is from `sacker`, not a discarded `def_slot`
3. Confirm `POSITION_DISTRIBUTION` sums to 85 (assert runs at import time — will raise if wrong)
4. Verify TURNOVER_INTERCEPTION and PASS_COMPLETE interceptor/tackler now picks from `DB or S` (expanded vs old `DB`-only)
5. Note pre-existing ruff errors — not introduced by this sprint, can be fixed in a cleanup sprint
