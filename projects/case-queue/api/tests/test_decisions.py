from __future__ import annotations

from httpx import AsyncClient

from app.models import Case

REVIEWER_HEADERS = {"x-actor-id": "alice", "x-actor-role": "reviewer"}
SENIOR_HEADERS = {"x-actor-id": "bob", "x-actor-role": "senior_reviewer"}


async def test_approve_updates_case_status(client: AsyncClient, seeded_case: Case) -> None:
    response = await client.post(
        f"/cases/{seeded_case.id}/decisions",
        json={"action": "approve", "notes": "Looks fine."},
        headers=REVIEWER_HEADERS,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["action"] == "approve"
    assert data["actor_id"] == "alice"

    case_response = await client.get(f"/cases/{seeded_case.id}")
    assert case_response.json()["status"] == "approved"


async def test_reject_updates_case_status(client: AsyncClient, seeded_case: Case) -> None:
    response = await client.post(
        f"/cases/{seeded_case.id}/decisions",
        json={"action": "reject", "notes": "Clear violation."},
        headers=REVIEWER_HEADERS,
    )
    assert response.status_code == 201
    assert response.json()["action"] == "reject"

    case_response = await client.get(f"/cases/{seeded_case.id}")
    assert case_response.json()["status"] == "rejected"


async def test_reviewer_cannot_escalate(client: AsyncClient, seeded_case: Case) -> None:
    response = await client.post(
        f"/cases/{seeded_case.id}/decisions",
        json={"action": "escalate", "notes": "Needs senior review."},
        headers=REVIEWER_HEADERS,
    )
    assert response.status_code == 403
    assert "escalate" in response.json()["detail"].lower()


async def test_senior_reviewer_can_escalate(client: AsyncClient, seeded_case: Case) -> None:
    response = await client.post(
        f"/cases/{seeded_case.id}/decisions",
        json={"action": "escalate", "notes": "Escalating to policy team."},
        headers=SENIOR_HEADERS,
    )
    assert response.status_code == 201
    assert response.json()["action"] == "escalate"

    case_response = await client.get(f"/cases/{seeded_case.id}")
    assert case_response.json()["status"] == "escalated"


async def test_empty_notes_rejected(client: AsyncClient, seeded_case: Case) -> None:
    response = await client.post(
        f"/cases/{seeded_case.id}/decisions",
        json={"action": "approve", "notes": ""},
        headers=REVIEWER_HEADERS,
    )
    assert response.status_code == 422


async def test_missing_actor_headers_rejected(client: AsyncClient, seeded_case: Case) -> None:
    response = await client.post(
        f"/cases/{seeded_case.id}/decisions",
        json={"action": "approve", "notes": "Fine."},
    )
    assert response.status_code == 422


async def test_decision_appears_in_case_detail(client: AsyncClient, seeded_case: Case) -> None:
    await client.post(
        f"/cases/{seeded_case.id}/decisions",
        json={"action": "approve", "notes": "All good."},
        headers=REVIEWER_HEADERS,
    )
    case_response = await client.get(f"/cases/{seeded_case.id}")
    decisions = case_response.json()["decisions"]
    assert len(decisions) == 1
    assert decisions[0]["notes"] == "All good."


async def test_invalid_role_rejected(client: AsyncClient, seeded_case: Case) -> None:
    response = await client.post(
        f"/cases/{seeded_case.id}/decisions",
        json={"action": "approve", "notes": "Fine."},
        headers={"x-actor-id": "charlie", "x-actor-role": "superadmin"},
    )
    assert response.status_code == 400
