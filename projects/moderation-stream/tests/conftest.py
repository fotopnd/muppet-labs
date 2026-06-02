from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from moderation_stream.api.database import get_session_factory, init_db
from moderation_stream.api.main import app

TEST_ASYNC_DB_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5433/moderation_stream_test"
)


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_ASYNC_DB_URL)
    await init_db(engine)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def api_client(test_engine):
    app.state.session_factory = get_session_factory(test_engine)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
