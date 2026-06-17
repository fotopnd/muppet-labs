from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from llm_safety_monitor.api.database import init_db
from llm_safety_monitor.api.routers import metrics, review, stream
from llm_safety_monitor.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    yield


app = FastAPI(title="LLM Safety Monitor", lifespan=lifespan)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.ALLOWED_ORIGINS.split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(metrics.router)
app.include_router(stream.router)
app.include_router(review.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def serve() -> None:
    settings = get_settings()
    uvicorn.run(
        "llm_safety_monitor.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
    )
