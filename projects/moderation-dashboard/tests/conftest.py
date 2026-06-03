from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from moderation_dashboard.api.database import get_session_factory, init_db
from moderation_dashboard.api.main import app
from moderation_dashboard.api.models import Classification

TEST_ASYNC_DB_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5434/moderation_dashboard_test"
)


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_ASYNC_DB_URL, poolclass=NullPool)
    await init_db(engine)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def api_client(test_engine):
    app.state.session_factory = get_session_factory(test_engine)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def seeded_classifications(test_engine):
    """Seed 10 shadow classification rows for 'distilbert' and 5 for 'roberta'."""
    now = datetime.now(UTC)
    rows = []

    for i in range(10):
        rows.append(
            Classification(
                id=str(uuid.uuid4()),
                event_id=str(uuid.uuid4()),
                group="shadow",
                model_name="distilbert",
                category="toxic",
                content="test content",
                predicted_label=1,
                confidence=0.85,
                latency_ms=float(20 + i * 5),
                correct=i < 8,  # 8/10 correct
                created_at=now,
            )
        )

    for i in range(5):
        rows.append(
            Classification(
                id=str(uuid.uuid4()),
                event_id=str(uuid.uuid4()),
                group="production",
                model_name="roberta",
                category="insult",
                content="test content",
                predicted_label=0,
                confidence=0.72,
                latency_ms=float(50 + i * 10),
                correct=i < 4,
                created_at=now,
            )
        )

    session_factory = get_session_factory(test_engine)
    async with session_factory() as session:
        session.add_all(rows)
        await session.commit()

    yield rows

    async with session_factory() as session:
        await session.execute(delete(Classification))
        await session.commit()
