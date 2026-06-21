from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from gridiron.api.routers import conglomerates, games, leaderboards, programs, schedule
from gridiron.api.routers import stream as stream_module
from gridiron.config import settings
from gridiron.database import engine, init_db, session_factory
from gridiron.orchestrator import season_loop, stream_game_replay

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    app.state.ticker_queues: list[asyncio.Queue] = []
    app.state.game_queues: dict[int, list[asyncio.Queue]] = {}
    app.state.session_factory = session_factory
    dev_replay = settings.dev_replay_game_id
    if dev_replay:
        loop_task = asyncio.create_task(stream_game_replay(dev_replay, app))
        app.state.replay_task = loop_task
        logger.info("Gridiron API started — DEV REPLAY game %d", dev_replay)
    else:
        loop_task = asyncio.create_task(season_loop(app))
        logger.info("Gridiron API started on port %d", settings.api_port)
    yield
    loop_task.cancel()
    await engine.dispose()
    logger.info("Gridiron API stopped")


app = FastAPI(title="Gridiron API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5177", settings.vite_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream_module.router)
app.include_router(conglomerates.router)
app.include_router(programs.router)
app.include_router(schedule.router)
app.include_router(games.router)
app.include_router(leaderboards.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/admin/replay")
async def admin_replay(request: Request) -> dict:
    game_id = settings.dev_replay_game_id
    if not game_id:
        return {"error": "no dev replay configured"}
    task = getattr(request.app.state, "replay_task", None)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE games SET status='scheduled', replay_started_at=NULL WHERE id=:id"),
            {"id": game_id},
        )
    new_task = asyncio.create_task(stream_game_replay(game_id, request.app))
    request.app.state.replay_task = new_task
    return {"ok": True}


def serve() -> None:
    import uvicorn

    uvicorn.run("gridiron.api.main:app", host="0.0.0.0", port=settings.api_port, reload=True)
