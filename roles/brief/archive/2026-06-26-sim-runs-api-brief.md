# Brief: sim-runs-api

**Role:** brief
**Sprint unit:** 03
**Project:** gridiron
**Date:** 2026-06-26
**Depends on:** unit 01 (migration), unit 02 (orchestrator)

---

## Context

15 `season=1` hardcodes across 6 API routers need to be replaced with `sim_run_id` filtering. A shared helper resolves the "active" sim run: the latest production run if one exists, else the latest non-discarded run. A new `sim_runs.py` router exposes management endpoints for creating runs, promoting, and discarding.

---

## Objective

- Add `gridiron/api/sim_run.py` helper module
- Update all 6 routers to filter by `sim_run_id` instead of `season=1`
- Add `gridiron/api/routers/sim_runs.py` with management endpoints
- Register the new router in `main.py`

---

## Specification

### 1. New file: `gridiron/api/sim_run.py`

```python
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def active_sim_run_id(db: AsyncSession) -> int:
    """Latest production run if any exist, else latest non-discarded run."""
    row = (await db.execute(text("""
        SELECT COALESCE(
            (SELECT id FROM sim_runs WHERE production_id IS NOT NULL ORDER BY production_id DESC LIMIT 1),
            (SELECT id FROM sim_runs WHERE status != 'discarded' ORDER BY id DESC LIMIT 1)
        )
    """))).scalar()
    if row is None:
        raise HTTPException(status_code=500, detail="No sim runs available")
    return int(row)
```

---

### 2. `gridiron/api/routers/conglomerates.py`

**File map:**

| Symbol | Approx line |
|---|---|
| `_WL_CTE` module-level string | 12 |
| `conglomerate_standings` endpoint | 46 |
| H2H query in `_h2h_wins` | ~15 (added in bug-fix sprint) |

**Changes:**

a) Update `_WL_CTE` — replace `season=1` with `:sim_run_id`:
```python
_WL_CTE = """
WITH wl AS (
    SELECT home_program_id AS pid,
           (home_score > away_score)::int AS won,
           (home_score < away_score)::int AS lost
    FROM games WHERE status='complete' AND sim_run_id=:sim_run_id
    UNION ALL
    SELECT away_program_id,
           (away_score > home_score)::int,
           (away_score < home_score)::int
    FROM games WHERE status='complete' AND sim_run_id=:sim_run_id
), wl_agg AS (
    SELECT pid, SUM(won)::int AS wins, SUM(lost)::int AS losses FROM wl GROUP BY pid
)
"""
```

b) Update `_h2h_wins` — add `sim_run_id` filter to the H2H query:
```python
async def _h2h_wins(db: AsyncSession, program_ids: list[int], sim_run_id: int) -> dict[int, int]:
    rows = (await db.execute(text("""
        SELECT CASE WHEN home_score > away_score THEN home_program_id
                    ELSE away_program_id END AS winner
        FROM games
        WHERE status = 'complete' AND sim_run_id = :sim_run_id
          AND home_program_id = ANY(:ids) AND away_program_id = ANY(:ids)
    """), {"ids": program_ids, "sim_run_id": sim_run_id})).fetchall()
    ...
```

c) Update `_sort_with_h2h` — pass `sim_run_id` through to `_h2h_wins`.

d) Update `conglomerate_standings` endpoint:
```python
from gridiron.api.sim_run import active_sim_run_id

@router.get("/conglomerates/{conglomerate_id}/standings", ...)
async def conglomerate_standings(conglomerate_id: int, db: AsyncSession = Depends(get_db)):
    run_id = await active_sim_run_id(db)
    # ... existing cong_row query unchanged ...
    rows = (await db.execute(
        text(f"{_WL_CTE} SELECT ..."),
        {"cid": conglomerate_id, "sim_run_id": run_id},
    )).mappings().all()
    tier1_raw = ...
    tier2_raw = ...
    tier1 = await _sort_with_h2h(db, tier1_raw, run_id)
    tier2 = await _sort_with_h2h(db, tier2_raw, run_id)
```

---

### 3. `gridiron/api/routers/programs.py`

**File map:**

| Symbol | Approx line |
|---|---|
| `_WL_CTE` module-level string | 73 |
| Program season stats query (`season=1`) | 98 |
| Program schedule query (`season=1`) | 184 |
| Player stats query (`season=1`) | 338 |

**Changes:**

a) Update `_WL_CTE` — same pattern as conglomerates, replace `season=1` with `:sim_run_id`.

b) In each endpoint that uses `season=1`:
- Call `run_id = await active_sim_run_id(db)` at top of function
- Replace `season=1` (or `g.season=1`) with `g.sim_run_id=:sim_run_id` (or `sim_run_id=:sim_run_id` where no alias)
- Add `"sim_run_id": run_id` to the params dict

c) Import: `from gridiron.api.sim_run import active_sim_run_id`

---

### 4. `gridiron/api/routers/games.py`

**File map:** lines 38 and 51 (`g.season=1`).

**Changes:** Call `run_id = await active_sim_run_id(db)`, replace `g.season=1` with `g.sim_run_id=:sim_run_id`, add `"sim_run_id": run_id` to `params`.

---

### 5. `gridiron/api/routers/schedule.py`

**File map:** lines 20 and 29 (`season=1` and `season=1`).

**Changes:** Same pattern — resolve run_id, replace both `season = 1` occurrences, add to params.

---

### 6. `gridiron/api/routers/nafca.py`

**File map:** lines 18 and 22 (`season = 1` in `_ELO_RANK_QUERY`).

`_ELO_RANK_QUERY` is a module-level `text()` constant. It cannot take parameters as a module-level constant. Change it to a string, and construct `text(...)` at call time with the `sim_run_id` param:

```python
_ELO_RANK_SQL = """
    WITH fg AS (
        SELECT program_id, pre_elo
        FROM (
            SELECT home_program_id AS program_id, home_elo_pre AS pre_elo,
                   ROW_NUMBER() OVER (PARTITION BY home_program_id ORDER BY week ASC) AS rn
            FROM games WHERE season_number = 1 AND home_elo_pre IS NOT NULL AND sim_run_id = :sim_run_id
            UNION ALL
            SELECT away_program_id, away_elo_pre,
                   ROW_NUMBER() OVER (PARTITION BY away_program_id ORDER BY week ASC) AS rn
            FROM games WHERE season_number = 1 AND away_elo_pre IS NOT NULL AND sim_run_id = :sim_run_id
        ) sub WHERE rn = 1
    )
    SELECT p.id, p.name, p.emoji, p.conglomerate_id, p.tier, p.elo,
           COALESCE(fg.pre_elo, p.elo) AS pre_season_elo,
           p.elo - COALESCE(fg.pre_elo, p.elo) AS season_delta
    FROM programs p LEFT JOIN fg ON fg.program_id = p.id
    ORDER BY p.elo DESC
"""
```

Note: `games` does not have a `season_number` column — the in-universe year is on `sim_runs`. Change `season_number = 1` filter to a JOIN: `JOIN sim_runs sr ON sr.id = games.sim_run_id AND sr.season_number = 1` or simplify to just filter by `sim_run_id = :sim_run_id` (no season_number filter needed — one run = one season). Drop the `season_number = 1` filter entirely; just use `sim_run_id = :sim_run_id`.

At the endpoint, call `run_id = await active_sim_run_id(db)` and pass `{"sim_run_id": run_id}`.

---

### 7. `gridiron/api/routers/leaderboards.py`

**File map:** line 24 (`g.season = :season`), line 33 (`season: int = Query(default=1)`).

**Changes:**
- Replace `season: int = Query(default=1)` with no season param (use `active_sim_run_id` instead)
- Replace `g.season = :season` with `g.sim_run_id = :sim_run_id`
- Add `"sim_run_id": run_id` to params

---

### 8. `gridiron/api/routers/coaches.py`

**File map:** `coach_games` CTE at line 39; `FROM games g WHERE ...` at line 48.

**Changes:** Add `AND g.sim_run_id = :sim_run_id` to the `coach_games` CTE WHERE clause. Resolve at endpoint level:

```python
from gridiron.api.sim_run import active_sim_run_id

@router.get("/coaches/{coach_id}", ...)
async def get_coach(coach_id: int, db: AsyncSession = Depends(get_db)):
    run_id = await active_sim_run_id(db)
    # ...
    season_rows = await db.execute(
        text("""WITH coach_games AS (
            SELECT g.id AS game_id, g.season, ...
            FROM games g
            WHERE (g.home_program_id = :pid OR g.away_program_id = :pid)
              AND g.status = 'complete'
              AND g.sim_run_id = :sim_run_id
        ), ...
        """),
        {"pid": pid, "sim_run_id": run_id},
    )
```

**Known limitation:** Coach history shows only one sim run at a time. Multi-season career history across multiple production runs will require a follow-up query that aggregates across all production sim_runs. Deferred.

---

### 9. New file: `gridiron/api/routers/sim_runs.py`

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gridiron.database import get_db

router = APIRouter(prefix="/sim-runs", tags=["sim-runs"])


class SimRunOut(BaseModel):
    id: int
    label: str
    season_number: int
    production_id: int | None
    production_name: str | None
    status: str
    notes: str | None

class SimRunCreate(BaseModel):
    label: str
    season_number: int = 1
    notes: str | None = None

class SimRunPromote(BaseModel):
    production_id: int
    production_name: str


@router.get("", response_model=list[SimRunOut])
async def list_sim_runs(db: AsyncSession = Depends(get_db)) -> list[SimRunOut]:
    rows = (await db.execute(text(
        "SELECT id, label, season_number, production_id, production_name, status, notes "
        "FROM sim_runs ORDER BY id DESC"
    ))).mappings().all()
    return [SimRunOut.model_validate(dict(r)) for r in rows]


@router.post("", response_model=SimRunOut, status_code=201)
async def create_sim_run(body: SimRunCreate, db: AsyncSession = Depends(get_db)) -> SimRunOut:
    row = (await db.execute(
        text("INSERT INTO sim_runs (label, season_number, notes) VALUES (:label, :season_number, :notes) RETURNING id, label, season_number, production_id, production_name, status, notes"),
        {"label": body.label, "season_number": body.season_number, "notes": body.notes},
    )).mappings().one()
    await db.commit()
    return SimRunOut.model_validate(dict(row))


@router.patch("/{run_id}/promote", response_model=SimRunOut)
async def promote_sim_run(run_id: int, body: SimRunPromote, db: AsyncSession = Depends(get_db)) -> SimRunOut:
    row = (await db.execute(
        text("UPDATE sim_runs SET production_id=:pid, production_name=:pname, status='complete' WHERE id=:id RETURNING id, label, season_number, production_id, production_name, status, notes"),
        {"pid": body.production_id, "pname": body.production_name, "id": run_id},
    )).mappings().one_or_none()
    if row is None:
        raise HTTPException(404, "sim run not found")
    await db.commit()
    return SimRunOut.model_validate(dict(row))


@router.delete("/{run_id}", status_code=204)
async def discard_sim_run(run_id: int, db: AsyncSession = Depends(get_db)) -> None:
    result = await db.execute(
        text("DELETE FROM sim_runs WHERE id=:id AND production_id IS NULL"),
        {"id": run_id},
    )
    if result.rowcount == 0:
        raise HTTPException(400, "cannot delete production run or run not found")
    await db.commit()
```

---

### 10. `gridiron/api/main.py`

Add import and register router:

```python
from gridiron.api.routers import sim_runs as sim_runs_module
# ...
app.include_router(sim_runs_module.router)
```

---

## Out of Scope

- Do not touch `gridiron/engine/` files
- Do not add game seeding to the `POST /sim-runs` endpoint — seeding is a separate scripts/ concern
- Frontend changes deferred — the API default (active run) means existing frontend continues to work

---

## Verification

```bash
# Restart backend after changes
pkill -f "uvicorn gridiron"
uv run uvicorn gridiron.api.main:app --port 8006 --reload &
sleep 3

# List sim runs
curl -s http://localhost:8006/sim-runs | python3 -m json.tool

# Standings still work
curl -s http://localhost:8006/conglomerates/1/standings | python3 -c "import sys,json; d=json.load(sys.stdin); print('tier1 count:', len(d['tier1']))"

# Games list
curl -s "http://localhost:8006/games?limit=5" | python3 -m json.tool | head -20

# Schedule
curl -s http://localhost:8006/schedule | python3 -m json.tool | head -10

# Leaderboards
curl -s http://localhost:8006/leaderboard/rushing?limit=5 | python3 -m json.tool

# NAFCA rankings
curl -s http://localhost:8006/nafca/rankings | python3 -m json.tool | head -20
```

---

## Handoff

Commit message: `feat: sim_run_id filtering across all API routers + sim-runs management endpoints`
After this unit: combined reviewer + retro for the full sprint.
