from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    import llm_safety_classifier

    from red_team_platform.config import get_settings
    from red_team_platform.db import create_engine, create_session_factory

    settings = get_settings()

    # Fail fast: load pair classifier at startup
    llm_safety_classifier.load(settings.pair_classifier_path)

    engine = create_engine(settings.database_url)
    app.state.session_factory = create_session_factory(engine)
    app.state.engine = engine

    logger.info("Red-team platform API started on port %d", settings.api_port)
    yield

    await engine.dispose()


def create_app() -> FastAPI:
    from red_team_platform.api.routers import (
        attacks,
        bias,
        clusters,
        coverage,
        regression,
        runs,
        sessions,
        strategy,
    )
    from red_team_platform.config import get_settings

    settings = get_settings()

    app = FastAPI(title="Red-Team Platform API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(attacks.router)
    app.include_router(runs.router)
    app.include_router(sessions.router)
    app.include_router(coverage.router)
    app.include_router(strategy.router)
    app.include_router(regression.router)
    app.include_router(clusters.router)
    app.include_router(bias.router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def run_server() -> None:
    import uvicorn

    from red_team_platform.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "red_team_platform.api.main:create_app",
        factory=True,
        host="0.0.0.0",
        port=settings.api_port,
        reload=True,
    )
