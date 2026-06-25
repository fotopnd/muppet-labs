from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import text

router = APIRouter()

_KEEPALIVE_INTERVAL = 25.0


async def _ticker_gen(request: Request) -> AsyncGenerator[str, None]:
    q: asyncio.Queue = asyncio.Queue(maxsize=500)
    request.app.state.ticker_queues.append(q)
    try:
        while True:
            if await request.is_disconnected():
                break
            try:
                data = await asyncio.wait_for(q.get(), timeout=_KEEPALIVE_INTERVAL)
            except TimeoutError:
                yield ": keepalive\n\n"
                continue
            if data is None:
                break
            yield f"data: {data}\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        try:
            request.app.state.ticker_queues.remove(q)
        except ValueError:
            pass


async def _game_gen(game_id: int, request: Request) -> AsyncGenerator[str, None]:
    q: asyncio.Queue = asyncio.Queue(maxsize=500)
    request.app.state.game_queues.setdefault(game_id, []).append(q)
    try:
        while True:
            if await request.is_disconnected():
                break
            try:
                data = await asyncio.wait_for(q.get(), timeout=_KEEPALIVE_INTERVAL)
            except TimeoutError:
                yield ": keepalive\n\n"
                continue
            if data is None:
                break
            yield f"data: {data}\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        try:
            request.app.state.game_queues[game_id].remove(q)
        except (ValueError, KeyError):
            pass


@router.get("/stream/ticker")
async def ticker_stream(request: Request) -> StreamingResponse:
    return StreamingResponse(
        _ticker_gen(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/games/{game_id}/stream")
async def game_stream(game_id: int, request: Request) -> StreamingResponse:
    db = request.app.state.session_factory
    async with db() as session:
        row = (
            await session.execute(
                text("SELECT status FROM games WHERE id=:gid"),
                {"gid": game_id},
            )
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if row[0] == "scheduled":
        raise HTTPException(status_code=409, detail="Game not yet started")

    return StreamingResponse(
        _game_gen(game_id, request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
