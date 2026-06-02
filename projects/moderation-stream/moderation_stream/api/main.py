from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from moderation_stream.api.database import (
    create_engine_from_settings,
    get_session_factory,
    init_db,
)
from moderation_stream.api.routers.metrics import router as metrics_router
from moderation_stream.config import Settings

_settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    engine = create_engine_from_settings(_settings)
    await init_db(engine)
    app.state.session_factory = get_session_factory(engine)
    yield
    await engine.dispose()


app = FastAPI(title="moderation-stream metrics", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[_settings.allowed_origin],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(metrics_router)


def run() -> None:
    import uvicorn

    uvicorn.run("moderation_stream.api.main:app", host="0.0.0.0", port=8001, reload=True)
