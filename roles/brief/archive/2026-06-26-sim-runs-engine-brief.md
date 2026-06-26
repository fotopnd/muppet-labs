# Brief: sim-runs-engine

**Role:** brief
**Sprint unit:** 02
**Project:** gridiron
**Date:** 2026-06-26
**Depends on:** unit 01 (sim-runs-migration)

---

## Context

`orchestrator.py` has three places that hardcode `season=1` when querying scheduled games. After unit 01, games have a `sim_run_id` column. The orchestrator must:

1. Resolve the active sim run at startup (latest `status='running'` row in `sim_runs`)
2. Replace `season=1` filters with `sim_run_id = :run_id`
3. Mark the sim run `complete` when no scheduled games remain
4. Support partial runs: if the engine is stopped mid-run, the sim_run stays `running` so a restart picks up where it left off

`gridiron/engine/game.py` does **not** need changes — it operates on individual games by ID; the sim_run_id is already on the game row.

---

## Objective

Update `gridiron/orchestrator.py` to be sim_run-aware: resolve active run at startup, filter queries by `sim_run_id`, mark run complete on finish.

---

## Specification

**File:** `gridiron/orchestrator.py` (tracked)

### File map

| Symbol | Approx line |
|---|---|
| `_first_pending_slot_offset(week)` | 112 |
| `season=1` in `_first_pending_slot_offset` | 119 |
| `season_loop(app)` | 129 |
| `season=1` in `season_loop` — `SELECT MIN(week)` | 138 |
| `season=1` in `season_loop` — `SELECT id FROM games` | 166 |

### Changes

**1. Add helper to resolve active sim_run_id** (insert near top of module, after imports):

```python
def _active_sim_run_id(conn) -> int | None:
    """Return the id of the latest running sim run, or None if none exists."""
    return conn.execute(
        text("SELECT id FROM sim_runs WHERE status = 'running' ORDER BY id DESC LIMIT 1")
    ).scalar()
```

**2. Update `_first_pending_slot_offset(week)`** — add `run_id` parameter and replace `season=1`:

```python
def _first_pending_slot_offset(week: int, run_id: int) -> int:
    sync_engine = create_engine(settings.sync_database_url)
    with Session(sync_engine) as session:
        conn = session.connection()
        for slot in SLOT_ORDER:
            has = conn.execute(
                text("SELECT 1 FROM games WHERE week=:w AND sim_run_id=:run_id AND status='scheduled' AND broadcast_slot=:s LIMIT 1"),
                {"w": week, "run_id": run_id, "s": slot},
            ).scalar()
            if has:
                sync_engine.dispose()
                return SLOT_OFFSETS[slot]
    sync_engine.dispose()
    return 0
```

**3. Update `season_loop(app)`:**

At the top of the while loop, resolve the active run:

```python
async def season_loop(app: FastAPI) -> None:
    loop = asyncio.get_running_loop()

    # Resolve active sim run once at startup
    sync_engine = create_engine(settings.sync_database_url)
    with Session(sync_engine) as session:
        run_id = _active_sim_run_id(session.connection())
    sync_engine.dispose()

    if run_id is None:
        logger.info("No running sim run found — season_loop exiting.")
        return

    logger.info("season_loop: active sim_run_id=%d", run_id)

    while True:
        sync_engine = create_engine(settings.sync_database_url)
        with Session(sync_engine) as session:
            conn = session.connection()
            next_week = conn.execute(
                text("SELECT MIN(week) FROM games WHERE sim_run_id=:run_id AND status='scheduled'"),
                {"run_id": run_id},
            ).scalar()
        sync_engine.dispose()

        if next_week is None:
            logger.info("Sim run %d complete — no scheduled games remain.", run_id)
            # Mark sim run complete
            sync_engine = create_engine(settings.sync_database_url)
            with Session(sync_engine) as session:
                session.connection().execute(
                    text("UPDATE sim_runs SET status='complete', completed_at=now() WHERE id=:run_id"),
                    {"run_id": run_id},
                )
                session.commit()
            sync_engine.dispose()
            break

        week = int(next_week)
        first_pending_offset = _first_pending_slot_offset(week, run_id)
        week_start = loop.time() - first_pending_offset
        logger.info("Starting week %d (first pending slot offset: %ds)", week, first_pending_offset)

        for slot in SLOT_ORDER:
            target = week_start + SLOT_OFFSETS[slot]
            sleep_sec = max(0.0, target - loop.time())
            if sleep_sec > 0:
                await asyncio.sleep(sleep_sec)

            sync_engine = create_engine(settings.sync_database_url)
            with Session(sync_engine) as session:
                conn = session.connection()
                game_ids = [
                    r[0] for r in conn.execute(
                        text(
                            "SELECT id FROM games "
                            "WHERE week=:w AND sim_run_id=:run_id AND status='scheduled' AND broadcast_slot=:s "
                            "ORDER BY id"
                        ),
                        {"w": week, "run_id": run_id, "s": slot},
                    ).fetchall()
                ]
            sync_engine.dispose()
            # ... rest of slot handling unchanged
```

Do not change anything below the `game_ids` query — the game execution, SSE fan-out, and logging are unchanged.

---

## Out of Scope

- Do not touch `gridiron/engine/game.py`
- Do not add a `create_sim_run` API endpoint — that is unit 03
- Do not change admin replay logic — it resets individual games by ID and is sim_run-agnostic

---

## Verification

```bash
# Confirm the DB has a running sim run (or mark one running for test)
uv run python3 -c "
import asyncio
from gridiron.database import engine
from sqlalchemy import text
async def main():
    async with engine.begin() as conn:
        r = await conn.execute(text('SELECT id, status FROM sim_runs'))
        print([dict(row) for row in r.mappings()])
asyncio.run(main())
"

# Check orchestrator picks up the run_id correctly by inspecting logs
# (start the API and watch for 'season_loop: active sim_run_id=1' in output)
uv run uvicorn gridiron.api.main:app --port 8006 2>&1 | grep -i "sim_run\|season_loop" | head -5
```

Expected: log line `season_loop: active sim_run_id=1` on startup.

---

## Handoff

Commit message: `feat: orchestrator resolves active sim_run, replaces season=1 hardcodes`
Next unit: 03 (sim-runs-api)
