from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from moderation_dashboard.api.database import (
    create_async_engine_from_url,
    get_session_factory,
    init_db,
)
from moderation_dashboard.api.routers.admin import router as admin_router
from moderation_dashboard.api.routers.cases import router as cases_router
from moderation_dashboard.api.routers.ingest import router as ingest_router
from moderation_dashboard.api.routers.metrics import router as metrics_router
from moderation_dashboard.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    engine = create_async_engine_from_url(settings.postgres_url_async)
    await init_db(engine)
    app.state.session_factory = get_session_factory(engine)
    yield
    await engine.dispose()


app = FastAPI(title="moderation-dashboard metrics API", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(metrics_router)
app.include_router(admin_router)
app.include_router(cases_router)
app.include_router(ingest_router)


def run() -> None:
    import uvicorn

    uvicorn.run(
        "moderation_dashboard.api.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
    )
