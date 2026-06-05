from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete as sa_delete
from sqlalchemy import select

from moderation_dashboard.api.database import get_session_factory
from moderation_dashboard.api.models import AnomalyFlag, Classification


@pytest_asyncio.fixture
async def admin_test_data(test_engine):
    """One seeded row, one live row, and one anomaly flag."""
    now = datetime.now(UTC)
    session_factory = get_session_factory(test_engine)

    seeded_row = Classification(
        id=str(uuid.uuid4()),
        event_id=str(uuid.uuid4()),
        group="production",
        model_name="distilbert",
        category="toxic",
        content="seeded content",
        predicted_label=1,
        confidence=0.9,
        latency_ms=20.0,
        correct=True,
        created_at=now,
        seeded=True,
    )
    live_row = Classification(
        id=str(uuid.uuid4()),
        event_id=str(uuid.uuid4()),
        group="production",
        model_name="distilbert",
        category="toxic",
        content="live content",
        predicted_label=1,
        confidence=0.8,
        latency_ms=25.0,
        correct=True,
        created_at=now,
        seeded=False,
    )
    flag = AnomalyFlag(
        id=str(uuid.uuid4()),
        window_start=now - timedelta(minutes=5),
        window_end=now,
        signal_name="error_rate",
        z_score=3.5,
        value=0.15,
        baseline_mean=0.05,
        baseline_std=0.02,
        created_at=now,
    )

    async with session_factory() as session:
        session.add_all([seeded_row, live_row, flag])
        await session.commit()

    yield {"seeded_id": seeded_row.id, "live_id": live_row.id, "flag_id": flag.id}

    async with session_factory() as session:
        await session.execute(sa_delete(Classification))
        await session.execute(sa_delete(AnomalyFlag))
        await session.commit()


async def test_restart_returns_204(api_client: AsyncClient) -> None:
    response = await api_client.post("/admin/restart")
    assert response.status_code == 204


async def test_restart_deletes_live_rows(
    api_client: AsyncClient, admin_test_data, test_engine
) -> None:
    await api_client.post("/admin/restart")
    session_factory = get_session_factory(test_engine)
    async with session_factory() as session:
        result = await session.execute(
            select(Classification).where(Classification.id == admin_test_data["live_id"])
        )
        assert result.scalar_one_or_none() is None


async def test_restart_preserves_seeded_rows(
    api_client: AsyncClient, admin_test_data, test_engine
) -> None:
    await api_client.post("/admin/restart")
    session_factory = get_session_factory(test_engine)
    async with session_factory() as session:
        result = await session.execute(
            select(Classification).where(Classification.id == admin_test_data["seeded_id"])
        )
        assert result.scalar_one_or_none() is not None


async def test_restart_clears_anomaly_flags(
    api_client: AsyncClient, admin_test_data, test_engine
) -> None:
    await api_client.post("/admin/restart")
    session_factory = get_session_factory(test_engine)
    async with session_factory() as session:
        result = await session.execute(
            select(AnomalyFlag).where(AnomalyFlag.id == admin_test_data["flag_id"])
        )
        assert result.scalar_one_or_none() is None
