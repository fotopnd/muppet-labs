from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from llm_safety_monitor.config import get_settings

_settings = get_settings()
_engine = create_async_engine(_settings.DATABASE_URL, echo=False)
_SessionLocal = async_sessionmaker(_engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _SessionLocal() as session:
        yield session


async def init_db() -> None:
    from llm_safety_monitor.api.models import Base

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
