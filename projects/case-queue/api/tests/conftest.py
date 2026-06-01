from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.models import Base, Case, CaseCategory, CaseStatus, Severity

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/case_queue_test",
)

_test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
_test_session_factory = async_sessionmaker(_test_engine, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db() -> AsyncGenerator[None, None]:
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await _test_engine.dispose()


@pytest.fixture(autouse=True)
async def truncate(setup_test_db: None) -> AsyncGenerator[None, None]:
    yield
    async with _test_engine.begin() as conn:
        await conn.execute(text("TRUNCATE cases, decisions RESTART IDENTITY CASCADE"))


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with _test_session_factory() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient wired to the FastAPI app with the test session injected."""
    import app.database as db_module

    original = db_module._session_factory
    db_module._session_factory = _test_session_factory
    db_module._engine = _test_engine

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    db_module._session_factory = original


@pytest.fixture
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
