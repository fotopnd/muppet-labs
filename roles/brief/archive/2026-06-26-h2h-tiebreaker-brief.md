# Brief: h2h-tiebreaker

**Role:** brief
**Sprint unit:** 02
**Project:** gridiron
**Date:** 2026-06-26

---

## Context

Conference standings in `conglomerates.py` sort by `wins DESC, losses ASC, p.elo DESC`. When two teams have identical W-L records the tiebreaker falls straight to ELO rating, which is not how college football standings work. The correct tiebreaker is head-to-head record: if tied teams played each other in the current season, the team that won that game ranks higher. ELO remains the final fallback.

---

## Objective

Add a head-to-head tiebreaker to conference standings. When two or more teams in the same tier have identical W-L records, sort them by H2H wins against each other, then ELO.

---

## Specification

**File:** `gridiron/api/routers/conglomerates.py`

### File map

| Symbol | File | Approx line |
|---|---|---|
| `_WL_CTE` | `gridiron/api/routers/conglomerates.py` | 12 |
| `conglomerate_standings` endpoint | `gridiron/api/routers/conglomerates.py` | 46 |
| SQL query with `ORDER BY` | `gridiron/api/routers/conglomerates.py` | 70–84 |
| tier1/tier2 list construction | `gridiron/api/routers/conglomerates.py` | 87–88 |

### Changes

**1. Add a helper function** above `conglomerate_standings`:

```python
async def _h2h_wins(db: AsyncSession, program_ids: list[int]) -> dict[int, int]:
    """Returns {program_id: h2h_wins} for games played within the given set."""
    if len(program_ids) < 2:
        return {}
    rows = (await db.execute(text("""
        SELECT CASE WHEN home_score > away_score THEN home_program_id
                    ELSE away_program_id END AS winner
        FROM games
        WHERE status = 'complete' AND season = 1
          AND home_program_id = ANY(:ids) AND away_program_id = ANY(:ids)
    """), {"ids": program_ids})).fetchall()
    counts: dict[int, int] = {pid: 0 for pid in program_ids}
    for (winner,) in rows:
        if winner in counts:
            counts[winner] += 1
    return counts
```

**2. Add a sort helper** that applies H2H within tied groups:

```python
async def _sort_with_h2h(db: AsyncSession, standings: list[ProgramStanding]) -> list[ProgramStanding]:
    result: list[ProgramStanding] = []
    i = 0
    while i < len(standings):
        j = i + 1
        while j < len(standings) and standings[j].wins == standings[i].wins and standings[j].losses == standings[i].losses:
            j += 1
        group = standings[i:j]
        if len(group) > 1:
            h2h = await _h2h_wins(db, [p.id for p in group])
            group.sort(key=lambda p: (-h2h.get(p.id, 0), -p.elo))
        result.extend(group)
        i = j
    return result
```

**3. Update `conglomerate_standings`** to call the sort helper:

Replace:
```python
    tier1 = [ProgramStanding.model_validate(dict(r)) for r in rows if r["tier"] == 1]
    tier2 = [ProgramStanding.model_validate(dict(r)) for r in rows if r["tier"] == 2]
```

With:
```python
    tier1_raw = [ProgramStanding.model_validate(dict(r)) for r in rows if r["tier"] == 1]
    tier2_raw = [ProgramStanding.model_validate(dict(r)) for r in rows if r["tier"] == 2]
    tier1 = await _sort_with_h2h(db, tier1_raw)
    tier2 = await _sort_with_h2h(db, tier2_raw)
```

**4. `ProgramStanding` needs `id` and `elo` fields.** Check `gridiron/api/schemas.py` — if `ProgramStanding` doesn't already expose `id` and `elo`, add them (the SQL already selects `p.id` and `p.elo`).

---

## Out of Scope

- Do not change the `_WL_CTE` SQL or the season hard-coding (`season = 1`) — season parameterisation is deferred
- Do not change `nafca.py` (ELO ranking is separate from standings)
- Do not touch any gitignored engine files

---

## Verification

```bash
# Find two teams in the same conference with the same W-L record
curl http://localhost:8006/conglomerates/1/standings | python3 -m json.tool | grep -A3 '"wins"'

# If none are tied naturally, you can check the SQL manually:
# SELECT conglomerate_id, wins, losses, COUNT(*) FROM (your standings query) GROUP BY 1,2,3 HAVING COUNT(*) > 1
```

If no ties exist in the current data, verify the code path by adding a unit test or temporarily hardcoding tied data. The function `_h2h_wins` can be called directly in a REPL to confirm the query returns sensible data.

---

## Handoff

Commit message: `fix: H2H tiebreaker in conference standings`
No dependency from units 01 or 03 — this unit is standalone.
