from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from year_zero.api.routers import analytics, cards, decisions, sessions
from year_zero.config import settings
from year_zero.database import engine, init_db, session_factory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    app.state.sse_queues = []
    app.state.session_factory = session_factory
    logger.info("Year Zero API started on port %d", settings.api_port)
    yield
    await engine.dispose()
    logger.info("Year Zero API stopped")


app = FastAPI(title="Year Zero API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175", settings.vite_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

# /cards/calibration must be registered before /cards/{phase} to avoid catch-all shadowing
app.include_router(cards.router)
app.include_router(sessions.router)
app.include_router(decisions.router)
app.include_router(analytics.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
