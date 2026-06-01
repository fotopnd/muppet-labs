from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.database import get_db
from app.main import app
from app.models import Base, Case, CaseCategory, CaseStatus, Severity

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/case_queue_test",
)


def _engine():
    """NullPool engine — fresh connection per call, no cross-loop state."""
    return create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)


# All fixtures are function-scoped so they share the same event loop as the
# test they serve. No session-scoped async fixtures → no loop mismatch.

@pytest_asyncio.fixture(autouse=True)
async def setup_and_teardown() -> AsyncGenerator[None, None]:
    """Create schema (no-op after first run), yield, then truncate."""
    engine = _engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

    yield

    engine = _engine()
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE cases, decisions RESTART IDENTITY CASCADE"))
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = _engine()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    engine = _engine()
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _get_test_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture
async def seeded_case(db_session: AsyncSession) -> Case:
    now = datetime.now(UTC)
    case = Case(
        id=str(uuid.uuid4()),
        content="You are an absolute disgrace.",
        category=CaseCategory.toxic,
        severity=Severity.high,
        status=CaseStatus.pending,
        source="test",
        meta={},
        created_at=now,
        updated_at=now,
    )
    db_session.add(case)
    await db_session.commit()
    await db_session.refresh(case)
    return case
