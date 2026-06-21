"""orchestrator.py — season loop + SSE fan-out.

Timing:
    WEEK_DURATION = 18000 s (5 hours)
    Slot offsets from week_start (seconds):
        noon       0
        afternoon  7200
        prime_time 12600
        late_night 16200
    Stream window per slot: ~600 s (EMIT_INTERVAL × PLAYS_PER_GAME)
"""
from __future__ import annotations

import asyncio
import json
import logging
from functools import partial

from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from gridiron.config import EMIT_INTERVAL, PLAYS_PER_GAME, settings

logger = logging.getLogger(__name__)

SLOT_ORDER = ["noon", "afternoon", "prime_time", "late_night"]
SLOT_OFFSETS: dict[str, int] = {
    "noon": 0,
    "afternoon": 7200,
    "prime_time": 12600,
    "late_night": 16200,
}
WEEK_DURATION = 18000


def _run_game_sync(game_id: int) -> None:
    from gridiron.engine.game import GameEngine  # lazy — avoids circular at import time

    engine = create_engine(settings.sync_database_url)
    with Session(engine) as session:
        conn = session.connection()
        conn.execute(text("DELETE FROM play_log WHERE game_id=:gid"), {"gid": game_id})
        GameEngine(game_id, conn).run()
        session.commit()
    engine.dispose()


async def stream_game_replay(game_id: int, app: FastAPI) -> None:
    """Read play_log for game_id and fan-out SSE events at EMIT_INTERVAL pace."""
    sync_engine = create_engine(settings.sync_database_url)
    with Session(sync_engine) as session:
        conn = session.connection()
        rows = conn.execute(
            text(
                "SELECT play_number, quarter, possession, play_type, yards_gained, "
                "field_pos_before, field_pos_after, score_home, score_away, "
                "primary_player_id, description, x_coord, y_coord, down, distance "
                "FROM play_log WHERE game_id=:gid ORDER BY play_number"
            ),
            {"gid": game_id},
        ).fetchall()
        # Set live + record wall-clock start so REST /plays can return only
        # plays emitted so far (broadcast model — same position for all clients).
        conn.execute(
            text("UPDATE games SET status='live', replay_started_at=now() WHERE id=:gid"),
            {"gid": game_id},
        )
        session.commit()
    sync_engine.dispose()

    for row in rows:
        payload = json.dumps({
            "game_id": game_id,
            "play_number": row[0],
            "quarter": row[1],
            "possession": row[2],
            "play_type": row[3],
            "yards_gained": row[4],
            "field_pos_before": row[5],
            "field_pos_after": row[6],
            "score_home": row[7],
            "score_away": row[8],
            "primary_player_id": row[9],
            "description": row[10],
            "x": row[11],
            "y": row[12],
            "down": row[13],
            "distance": row[14],
        })
        # Fresh lookup each play so clients who connect mid-replay are included
        for q in list(app.state.game_queues.get(game_id, [])):
            await q.put(payload)
        for q in list(app.state.ticker_queues):
            await q.put(payload)
        await asyncio.sleep(EMIT_INTERVAL)

    # Sentinel: signal end-of-game to per-game clients; mark complete in DB
    for q in list(app.state.game_queues.get(game_id, [])):
        await q.put(None)

    sync_engine = create_engine(settings.sync_database_url)
    with Session(sync_engine) as session:
        session.connection().execute(
            text("UPDATE games SET status='complete' WHERE id=:gid"),
            {"gid": game_id},
        )
        session.commit()
    sync_engine.dispose()


def _first_pending_slot_offset(week: int) -> int:
    """Return SLOT_OFFSETS of the first slot that still has scheduled games."""
    sync_engine = create_engine(settings.sync_database_url)
    with Session(sync_engine) as session:
        conn = session.connection()
        for slot in SLOT_ORDER:
            has = conn.execute(
                text("SELECT 1 FROM games WHERE week=:w AND season=1 AND status='scheduled' AND broadcast_slot=:s LIMIT 1"),
                {"w": week, "s": slot},
            ).scalar()
            if has:
                sync_engine.dispose()
                return SLOT_OFFSETS[slot]
    sync_engine.dispose()
    return 0


async def season_loop(app: FastAPI) -> None:
    """Asyncio task: advances weekly slates until all games are played."""
    loop = asyncio.get_running_loop()

    while True:
        sync_engine = create_engine(settings.sync_database_url)
        with Session(sync_engine) as session:
            conn = session.connection()
            next_week = conn.execute(
                text("SELECT MIN(week) FROM games WHERE season=1 AND status='scheduled'")
            ).scalar()
        sync_engine.dispose()

        if next_week is None:
            logger.info("Season complete — no scheduled games remain.")
            break

        week = int(next_week)
        # On restart, backdate week_start so the first pending slot fires immediately
        # rather than sleeping its full offset from now.
        first_pending_offset = _first_pending_slot_offset(week)
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
                            "WHERE week=:w AND season=1 AND status='scheduled' AND broadcast_slot=:s "
                            "ORDER BY id"
                        ),
                        {"w": week, "s": slot},
                    ).fetchall()
                ]
            sync_engine.dispose()

            if not game_ids:
                continue

            logger.info("Week %d %s: %d games", week, slot, len(game_ids))

            # Run all games in executor concurrently
            await asyncio.gather(*[
                loop.run_in_executor(None, _run_game_sync, gid)
                for gid in game_ids
            ])

            # Spawn replay tasks (non-blocking — run concurrently with next slot sleep)
            for gid in game_ids:
                asyncio.create_task(stream_game_replay(gid, app))

        # Sleep through end of week before starting next
        week_end = week_start + WEEK_DURATION
        remaining = max(0.0, week_end - loop.time())
        if remaining > 0:
            await asyncio.sleep(remaining)
