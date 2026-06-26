# Brief: offseason-api-stubs

**Role:** brief
**Sprint unit:** 03
**Project:** gridiron
**Date:** 2026-06-26

---

## Context

Phase 1 needs three working endpoints: a generate-prospects trigger, a prospects list, and a portal entries list. The Phase 2 simulation endpoints (graduation, portal resolution, recruiting, training camp) are stubbed with 501 responses so the router is in place and can be filled by Phase 2 units without changing routing.

---

## Objective

Create `gridiron/api/routers/offseason.py` with 3 live endpoints and 4 Phase-2 stubs. Register the router in `main.py`.

---

## Specification

### New file: `gridiron/api/routers/offseason.py`

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from gridiron.api.sim_run import active_sim_run_id
from gridiron.database import get_db, engine

router = APIRouter(prefix="/offseason", tags=["offseason"])


# --- Schemas ---

class ProspectOut(BaseModel):
    id: int
    sim_run_id: int
    season_number: int
    first_name: str
    last_name: str
    position: str
    home_state: str
    rating: int
    prestige: int
    status: str
    committed_program_id: int | None


class PortalEntryOut(BaseModel):
    id: int
    sim_run_id: int
    season_number: int
    player_id: int
    reason: str
    status: str


class GenerateProspectsBody(BaseModel):
    season_number: int
    sim_run_id: int | None = None  # defaults to active run


class GenerateProspectsResult(BaseModel):
    inserted: int
    sim_run_id: int
    season_number: int


# --- Live endpoints ---

@router.post("/generate-prospects", response_model=GenerateProspectsResult, status_code=201)
async def generate_prospects_endpoint(
    body: GenerateProspectsBody,
    db: AsyncSession = Depends(get_db),
) -> GenerateProspectsResult:
    run_id = body.sim_run_id or await active_sim_run_id(db)

    # Guard: refuse if already generated for this run+season
    existing = (await db.execute(
        text("SELECT COUNT(*) FROM prospects WHERE sim_run_id=:rid AND season_number=:sn"),
        {"rid": run_id, "sn": body.season_number},
    )).scalar() or 0
    if existing > 0:
        raise HTTPException(400, f"prospects already generated for run {run_id} season {body.season_number} ({existing} rows) — delete first if you want to regenerate")

    from gridiron.engine.offseason import generate_prospects  # lazy import: gitignored
    async with engine.begin() as conn:
        n = await generate_prospects(run_id, body.season_number, conn)

    return GenerateProspectsResult(inserted=n, sim_run_id=run_id, season_number=body.season_number)


@router.get("/prospects", response_model=list[ProspectOut])
async def list_prospects(
    season_number: int | None = None,
    position: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[ProspectOut]:
    run_id = await active_sim_run_id(db)

    filters = ["sim_run_id = :rid"]
    params: dict = {"rid": run_id}
    if season_number is not None:
        filters.append("season_number = :sn")
        params["sn"] = season_number
    if position is not None:
        filters.append("position = :pos")
        params["pos"] = position

    where = " AND ".join(filters)
    rows = (await db.execute(
        text(f"SELECT id, sim_run_id, season_number, first_name, last_name, position, home_state, rating, prestige, status, committed_program_id FROM prospects WHERE {where} ORDER BY prestige DESC, rating DESC LIMIT 500"),
        params,
    )).mappings().all()
    return [ProspectOut.model_validate(dict(r)) for r in rows]


@router.get("/portal", response_model=list[PortalEntryOut])
async def list_portal(
    season_number: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[PortalEntryOut]:
    run_id = await active_sim_run_id(db)

    filters = ["sim_run_id = :rid"]
    params: dict = {"rid": run_id}
    if season_number is not None:
        filters.append("season_number = :sn")
        params["sn"] = season_number

    where = " AND ".join(filters)
    rows = (await db.execute(
        text(f"SELECT id, sim_run_id, season_number, player_id, reason, status FROM portal_entries WHERE {where} ORDER BY id"),
        params,
    )).mappings().all()
    return [PortalEntryOut.model_validate(dict(r)) for r in rows]


# --- Phase 2 stubs (filled by later units) ---

@router.post("/run-graduation", status_code=501)
async def run_graduation() -> dict:
    raise HTTPException(501, "not implemented — Phase 2 unit 04")


@router.post("/run-portal", status_code=501)
async def run_portal() -> dict:
    raise HTTPException(501, "not implemented — Phase 2 unit 04")


@router.post("/run-recruiting", status_code=501)
async def run_recruiting() -> dict:
    raise HTTPException(501, "not implemented — Phase 2 unit 05")


@router.post("/run-training-camp", status_code=501)
async def run_training_camp() -> dict:
    raise HTTPException(501, "not implemented — Phase 2 unit 06")
```

### Edit: `gridiron/api/main.py`

Import and register the new router alongside the existing ones:

```python
from gridiron.api.routers import offseason as offseason_module
# ...
app.include_router(offseason_module.router)
```

---

## Notes

- **Lazy import** of `gridiron.engine.offseason`: this module is gitignored and won't exist in a clean checkout. Importing at module level would break the API on import. Import inside the endpoint body so the rest of the router works without the engine file.
- **engine.begin() vs db session**: `generate_prospects` takes a raw `AsyncConnection` for bulk insert. The `engine` is imported from `gridiron.database` separately from `get_db`. Both `db` (session) and `engine` (connection) are available — use `db` for read queries, `engine.begin()` for the bulk insert call.
- **LIMIT 500** on prospects list: 2500 rows is fine for a tool endpoint; add pagination when this becomes a user-facing player picker.
- **Phase 2 stubs return 501**: preferred over 404 or 422 — signals "exists but not yet implemented." Phase 2 units replace the stub body, not the route signature.
- **No sim_run_id query param on list endpoints**: both prospects and portal default to `active_sim_run_id()`. Add explicit filtering only if needed.

---

## Out of Scope

- No frontend changes this unit
- No simulation logic — stubs only for Phase 2 routes
- No DELETE /offseason/prospects (not needed yet — YAGNI)

---

## Verification

```bash
# 1. Migration must be applied (unit 01 prerequisite)
uv run alembic upgrade head

# 2. Start backend
uv run uvicorn gridiron.api.main:app --port 8006 --reload

# 3. Generate prospects
curl -s -X POST http://localhost:8006/offseason/generate-prospects \
  -H "Content-Type: application/json" \
  -d '{"season_number": 2}' | python3 -m json.tool
# Expected: {"inserted": 2500, "sim_run_id": 1, "season_number": 2}

# 4. List prospects (should return up to 500 sorted by prestige/rating)
curl -s "http://localhost:8006/offseason/prospects?season_number=2" | python3 -m json.tool | head -40

# 5. Duplicate guard
curl -s -X POST http://localhost:8006/offseason/generate-prospects \
  -H "Content-Type: application/json" \
  -d '{"season_number": 2}'
# Expected: 400 "prospects already generated..."

# 6. Portal list (empty for now)
curl -s "http://localhost:8006/offseason/portal" | python3 -m json.tool
# Expected: []

# 7. Phase 2 stubs
curl -s -X POST http://localhost:8006/offseason/run-graduation
# Expected: 501
```

---

## Handoff

Commit message: `feat: offseason API — generate-prospects trigger, prospects list, portal list, Phase 2 stubs`
Phase 1 complete. Phase 2 planning is a separate sprint.
