from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete as sa_delete

from moderation_dashboard.api.database import get_session_factory
from moderation_dashboard.api.models import CaseDecision, Classification, Escalation


@pytest_asyncio.fixture
async def case_data(test_engine):
    """One escalation paired with a matching classification row."""
    now = datetime.now(UTC)
    session_factory = get_session_factory(test_engine)
    event_id = str(uuid.uuid4())

    classification = Classification(
        id=str(uuid.uuid4()),
        event_id=event_id,
        group="production",
        model_name="distilbert",
        category="threat",
        content="threatening content",
        predicted_label=1,
        confidence=0.91,
        latency_ms=22.0,
        correct=True,
        created_at=now,
        seeded=True,
    )
    escalation = Escalation(
        id=str(uuid.uuid4()),
        event_id=event_id,
        case_queue_case_id=str(uuid.uuid4()),
        escalation_reason="low_confidence",
        confidence_max=0.91,
        created_at=now,
    )

    async with session_factory() as session:
        session.add_all([classification, escalation])
        await session.commit()

    yield {"escalation_id": escalation.id, "event_id": event_id}

    async with session_factory() as session:
        await session.execute(sa_delete(CaseDecision))
        await session.execute(sa_delete(Escalation))
        await session.execute(sa_delete(Classification))
        await session.commit()


async def test_list_cases_empty(api_client: AsyncClient) -> None:
    response = await api_client.get("/cases")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_cases_returns_content(api_client: AsyncClient, case_data) -> None:
    response = await api_client.get("/cases")
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) == 1
    case = cases[0]
    assert case["id"] == case_data["escalation_id"]
    assert case["content"] == "threatening content"
    assert case["category"] == "threat"
    assert case["escalation_reason"] == "low_confidence"
    assert case["action"] is None


async def test_create_decision(api_client: AsyncClient, case_data) -> None:
    esc_id = case_data["escalation_id"]
    response = await api_client.post(
        f"/cases/{esc_id}/decide",
        json={"action": "approved", "notes": "looks fine"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["escalation_id"] == esc_id
    assert data["action"] == "approved"
    assert data["notes"] == "looks fine"


async def test_create_decision_409_duplicate(api_client: AsyncClient, case_data) -> None:
    esc_id = case_data["escalation_id"]
    await api_client.post(f"/cases/{esc_id}/decide", json={"action": "approved"})
    response = await api_client.post(f"/cases/{esc_id}/decide", json={"action": "rejected"})
    assert response.status_code == 409


async def test_create_decision_404_unknown(api_client: AsyncClient) -> None:
    response = await api_client.post(
        f"/cases/{uuid.uuid4()}/decide",
        json={"action": "approved"},
    )
    assert response.status_code == 404
