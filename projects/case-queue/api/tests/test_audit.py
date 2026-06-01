from __future__ import annotations

from httpx import AsyncClient

from app.models import Case

REVIEWER_HEADERS = {"x-actor-id": "alice", "x-actor-role": "reviewer"}
SENIOR_HEADERS = {"x-actor-id": "bob", "x-actor-role": "senior_reviewer"}


async def test_audit_log_empty(client: AsyncClient) -> None:
    response = await client.get("/audit-log")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


async def test_audit_log_records_decision(client: AsyncClient, seeded_case: Case) -> None:
    await client.post(
        f"/cases/{seeded_case.id}/decisions",
        json={"action": "approve", "notes": "Approved."},
        headers=REVIEWER_HEADERS,
    )
    response = await client.get("/audit-log")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    entry = data["items"][0]
    assert entry["case_id"] == seeded_case.id
    assert entry["actor_id"] == "alice"
    assert entry["action"] == "approve"


async def test_audit_log_filter_by_action(client: AsyncClient, seeded_case: Case) -> None:
    await client.post(
        f"/cases/{seeded_case.id}/decisions",
        json={"action": "approve", "notes": "Approved."},
        headers=REVIEWER_HEADERS,
    )
    await client.post(
        f"/cases/{seeded_case.id}/decisions",
        json={"action": "escalate", "notes": "Escalated."},
        headers=SENIOR_HEADERS,
    )

    response = await client.get("/audit-log?action=approve")
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["action"] == "approve"


async def test_audit_log_filter_by_actor(client: AsyncClient, seeded_case: Case) -> None:
    await client.post(
        f"/cases/{seeded_case.id}/decisions",
        json={"action": "approve", "notes": "By alice."},
        headers=REVIEWER_HEADERS,
    )
    await client.post(
        f"/cases/{seeded_case.id}/decisions",
        json={"action": "escalate", "notes": "By bob."},
        headers=SENIOR_HEADERS,
    )

    response = await client.get("/audit-log?actor_id=bob")
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["actor_id"] == "bob"


async def test_audit_log_pagination(client: AsyncClient, seeded_case: Case) -> None:
    for i in range(5):
        await client.post(
            f"/cases/{seeded_case.id}/decisions",
            json={"action": "approve", "notes": f"Decision {i}"},
            headers=REVIEWER_HEADERS,
        )

    response = await client.get("/audit-log?page=1&page_size=3")
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 3
