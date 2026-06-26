# Brief: prospect-generation

**Role:** brief
**Sprint unit:** 02
**Project:** gridiron
**Date:** 2026-06-26

---

## Context

The recruit pool for each off-season must exist before recruiting logic runs. Generating prospects is **not automatic** on sim_run creation — alpha tuning runs don't need them. Instead, `generate_prospects` is an explicit trigger called when the user is ready to run a full off-season.

Prospects are fictitious recruits with home states, positions, and prestige ratings. The pool is intentionally oversupplied: there should always be more available prospects than empty roster spots across all programs.

---

## Objective

Create `gridiron/engine/offseason.py` (gitignored) with a `generate_prospects` function. Wire it to a `POST /offseason/generate-prospects` endpoint (unit 03 owns the router file; unit 02 owns the engine file only).

---

## Specification

### New file: `gridiron/engine/offseason.py` (GITIGNORED)

```python
"""Off-season simulation engine."""
from __future__ import annotations

import random
from sqlalchemy import text

# Position distribution for prospect pool
# Roughly mirrors roster composition needs
_POSITION_WEIGHTS = {
    "QB": 5, "WR": 12, "RB": 8, "TE": 6,
    "OL": 20, "DL": 14, "LB": 12, "CB": 10,
    "SS": 5, "FS": 5, "K": 2, "P": 1,
}

_POSITIONS = list(_POSITION_WEIGHTS.keys())
_WEIGHTS   = [_POSITION_WEIGHTS[p] for p in _POSITIONS]

# US states + DC (abbreviations)
_STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC",
]

# State weight: FL, TX, CA, OH, GA get higher share (real recruiting hotbeds)
_STATE_WEIGHTS = {s: 1 for s in _STATES}
for hot in ("FL","TX","CA","OH","GA","PA","NJ","VA","LA","TN"):
    _STATE_WEIGHTS[hot] = 4
_STATE_W_LIST = [_STATE_WEIGHTS[s] for s in _STATES]

# First/last name pools (short; enough for 2500 unique combos)
_FIRST = [
    "James","John","Robert","Michael","William","David","Richard","Joseph","Thomas",
    "Marcus","Andre","DeShawn","Malik","Darius","Tyrese","Jalen","Jordan","Justin",
    "Tyler","Brandon","Cade","Eli","Bo","Trae","Isaiah","Xavier","Kendall","Devon",
    "Caleb","Noah","Ethan","Liam","Owen","Miles","Chase","Cole","Bryce","Grayson",
]
_LAST = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Wilson",
    "Moore","Taylor","Anderson","Thomas","Jackson","White","Harris","Martin","Thompson",
    "Robinson","Clark","Lewis","Lee","Walker","Hall","Allen","Young","Hernandez","King",
    "Wright","Hill","Scott","Green","Adams","Baker","Nelson","Carter","Mitchell","Perez",
    "Roberts","Turner","Phillips","Campbell","Parker","Evans","Edwards","Collins","Stewart",
]


def _prestige_from_rating(rating: int) -> int:
    """Map 1-100 rating to 1-5 star prestige. Skewed low."""
    if rating >= 90: return 5
    if rating >= 78: return 4
    if rating >= 65: return 3
    if rating >= 50: return 2
    return 1


async def generate_prospects(sim_run_id: int, season_number: int, conn) -> int:
    """
    Generate ~2500 prospects for the given sim_run + season.
    Returns the number of prospects inserted.
    """
    rng = random.Random(sim_run_id * 99991 + season_number * 31337)

    rows = []
    for _ in range(2500):
        position = rng.choices(_POSITIONS, weights=_WEIGHTS, k=1)[0]
        home_state = rng.choices(_STATES, weights=_STATE_W_LIST, k=1)[0]
        # Rating: skew toward lower end (most recruits are average)
        rating = min(100, max(40, int(rng.gauss(62, 14))))
        prestige = _prestige_from_rating(rating)
        rows.append({
            "sim_run_id": sim_run_id,
            "season_number": season_number,
            "first_name": rng.choice(_FIRST),
            "last_name": rng.choice(_LAST),
            "position": position,
            "home_state": home_state,
            "rating": rating,
            "prestige": prestige,
        })

    await conn.execute(
        text("""
            INSERT INTO prospects
                (sim_run_id, season_number, first_name, last_name,
                 position, home_state, rating, prestige)
            VALUES
                (:sim_run_id, :season_number, :first_name, :last_name,
                 :position, :home_state, :rating, :prestige)
        """),
        rows,
    )
    return len(rows)
```

---

## Notes

- **Deterministic by seed**: `random.Random(sim_run_id * 99991 + season_number * 31337)` — same run + season always generates the same pool. Useful for debugging.
- **2500 prospects**: ~130 programs × ~15 empty spots per year ≈ 1950 spots total, so 2500 gives ~28% surplus. Adjust later if needed.
- **Rating distribution**: Gaussian centred at 62 with σ=14, clamped to 40–100. Gives roughly: 5★ ~5%, 4★ ~15%, 3★ ~30%, 2★ ~30%, 1★ ~20%. Intentionally skewed low.
- **Name collisions**: With 38 first names × 46 last names = 1748 unique full names — expect duplicates at 2500. Fine for fiction.
- **`conn` parameter**: Pass an `AsyncConnection` (SQLAlchemy async engine `begin()` context), not a session. The endpoint in unit 03 uses `async with engine.begin() as conn`.
- **No dedup guard**: If called twice for the same sim_run_id + season_number, creates a second batch. The endpoint in unit 03 should check for existing prospects before calling.

---

## Out of Scope

- No roster logic, no signing, no portal — Phase 2
- No API router — that's unit 03
- Do not write to `players` — prospects are a separate pool until signed

---

## Verification

After unit 03 adds the endpoint, test end-to-end via:
```bash
curl -X POST http://localhost:8006/offseason/generate-prospects \
  -H "Content-Type: application/json" \
  -d '{"sim_run_id": 1, "season_number": 2}'
```
Expected: `{"inserted": 2500}` and `SELECT COUNT(*) FROM prospects WHERE sim_run_id=1` → 2500.

For unit-level check (no endpoint yet), engine can be called via quick script:
```python
import asyncio
from gridiron.database import engine
from gridiron.engine.offseason import generate_prospects
from sqlalchemy import text

async def main():
    async with engine.begin() as conn:
        n = await generate_prospects(1, 2, conn)
        print(f"inserted {n}")
        r = await conn.execute(text("SELECT prestige, COUNT(*) FROM prospects WHERE sim_run_id=1 GROUP BY prestige ORDER BY prestige"))
        for row in r.mappings():
            print(dict(row))

asyncio.run(main())
```

---

## Handoff

Commit message: `feat: generate_prospects engine function — 2500 prospect pool per season`
Unit 03 (offseason-api-stubs) wires this to `POST /offseason/generate-prospects`.
