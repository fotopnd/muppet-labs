from __future__ import annotations

import uuid
from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Case, CaseCategory, CaseStatus, Severity


async def test_list_cases_empty(client: AsyncClient) -> None:
    response = await client.get("/cases")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["page"] == 1


async def test_list_cases_returns_items(client: AsyncClient, seeded_case: Case) -> None:
    response = await client.get("/cases")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == seeded_case.id


async def test_list_cases_filter_by_category(
    client: AsyncClient, db_session: AsyncSession, seeded_case: Case
) -> None:
    # Add a case with a different category
    now = datetime.now(UTC)
    other = Case(
        id=str(uuid.uuid4()),
        content="Test",
        category=CaseCategory.threat,
        severity=Severity.low,
        status=CaseStatus.pending,
        source="test",
        meta={},
        created_at=now,
        updated_at=now,
    )
    db_session.add(other)
    await db_session.commit()

    response = await client.get("/cases?category=toxic")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["category"] == "toxic"


async def test_list_cases_pagination(client: AsyncClient, db_session: AsyncSession) -> None:
    now = datetime.now(UTC)
    for i in range(5):
        db_session.add(
            Case(
                id=str(uuid.uuid4()),
                content=f"Case {i}",
                category=CaseCategory.insult,
                severity=Severity.medium,
                status=CaseStatus.pending,
                source="test",
                meta={},
                created_at=now,
                updated_at=now,
            )
        )
    await db_session.commit()

    response = await client.get("/cases?page=1&page_size=3")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 3
    assert data["page"] == 1
    assert data["page_size"] == 3


async def test_get_case_found(client: AsyncClient, seeded_case: Case) -> None:
    response = await client.get(f"/cases/{seeded_case.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == seeded_case.id
    assert data["content"] == seeded_case.content
    assert data["decisions"] == []


async def test_get_case_not_found(client: AsyncClient) -> None:
    response = await client.get("/cases/nonexistent-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


async def test_create_case_returns_201(client: AsyncClient) -> None:
    response = await client.post(
        "/cases",
        json={
            "content": "This is offensive content.",
            "category": "toxic",
            "severity": "high",
            "source": "api-test",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["content"] == "This is offensive content."
    assert data["category"] == "toxic"
    assert data["decisions"] == []


async def test_create_case_appears_in_queue(client: AsyncClient) -> None:
    await client.post(
        "/cases",
        json={
            "content": "Hate speech example.",
            "category": "identity_hate",
            "severity": "high",
            "source": "test",
        },
    )
    response = await client.get("/cases?status=pending")
    assert response.json()["total"] >= 1


async def test_create_case_missing_fields_rejected(client: AsyncClient) -> None:
    response = await client.post("/cases", json={"content": "Missing category and severity."})
    assert response.status_code == 422


async def test_list_cases_filter_by_source(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    now = datetime.now(UTC)
    for source in ("moderation-dashboard", "manual-review", "moderation-dashboard"):
        db_session.add(
            Case(
                id=str(uuid.uuid4()),
                content="Test content",
                category=CaseCategory.toxic,
                severity=Severity.medium,
                status=CaseStatus.pending,
                source=source,
                meta={},
                created_at=now,
                updated_at=now,
            )
        )
    await db_session.commit()

    response = await client.get("/cases?source=moderation-dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["source"] == "moderation-dashboard" for item in data["items"])
