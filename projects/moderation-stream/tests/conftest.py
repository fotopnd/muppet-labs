from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine

from moderation_stream.api.database import get_session_factory, init_db
from moderation_stream.api.main import app
from moderation_stream.api.models import ClassificationResult

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


@pytest_asyncio.fixture
async def seeded_results(test_engine):
    """Insert 10 known ClassificationResult rows and clean up after the test.

    10 rows for distilbert-zero-shot; latencies 10–100 ms; 8 correct → accuracy 0.8, p50 55.0 ms.
    """
    latencies = [float(i * 10) for i in range(1, 11)]
    rows = [
        ClassificationResult(
            event_id=str(uuid.uuid4()),
            model_name="distilbert-zero-shot",
            predicted_label=1,
            latency_ms=latencies[i],
            correct=(i < 8),
            processed_at=datetime.now(UTC),
        )
        for i in range(10)
    ]

    session_factory = get_session_factory(test_engine)
    async with session_factory() as session:
        session.add_all(rows)
        await session.commit()

    yield rows

    async with session_factory() as session:
        await session.execute(
            delete(ClassificationResult).where(
                ClassificationResult.model_name == "distilbert-zero-shot"
            )
        )
        await session.commit()
