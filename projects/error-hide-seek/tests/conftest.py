import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://ehs:ehs@localhost:5436/error_hide_seek_test"
)
os.environ.setdefault(
    "SYNC_DATABASE_URL", "postgresql+psycopg2://ehs:ehs@localhost:5436/error_hide_seek_test"
)
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from error_hide_seek.api.deps import get_db
from error_hide_seek.api.main import app
from error_hide_seek.models import Base

TEST_DB_URL = os.environ["DATABASE_URL"]

_TRUNCATE_SQL = text(
    "TRUNCATE human_detections, agent_annotations, review_sessions, "
    "planted_errors, experiment_papers, experiments, papers RESTART IDENTITY CASCADE"
)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    import asyncio

    async def _init():
        engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(_init())


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        await session.execute(_TRUNCATE_SQL)
        await session.commit()
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
