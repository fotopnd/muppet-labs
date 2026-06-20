from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gridiron.config import settings
from gridiron.database import engine, init_db, session_factory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    app.state.sse_queues = []
    app.state.session_factory = session_factory
    logger.info("Gridiron API started on port %d", settings.api_port)
    yield
    await engine.dispose()
    logger.info("Gridiron API stopped")


app = FastAPI(title="Gridiron API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5177", settings.vite_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers registered here by the implementer role.


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


def serve() -> None:
    import uvicorn
    uvicorn.run("gridiron.api.main:app", host="0.0.0.0", port=settings.api_port, reload=True)
