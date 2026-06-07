from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from error_hide_seek.api.routers import experiments, health, papers, results, reviews, sessions
from error_hide_seek.config import settings
from error_hide_seek.db import engine, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(title="Error-Hide-Seek API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(papers.router)
app.include_router(experiments.router)
app.include_router(sessions.router)
app.include_router(reviews.router)
app.include_router(results.router)


def run() -> None:
    uvicorn.run("error_hide_seek.api.main:app", host="0.0.0.0", port=settings.api_port, reload=True)
