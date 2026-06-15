from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from year_zero.models import DocumentLibrary


@pytest.mark.asyncio
async def test_batch_decisions(client: AsyncClient, seeded_library: list[DocumentLibrary]) -> None:
    # Create session
    create_resp = await client.post("/sessions", json={"started_at": datetime.now(UTC).isoformat()})
    session_id = create_resp.json()["session_id"]

    doc_id = seeded_library[1].id  # phase-1 tier-1 card

    payload = {
        "session_id": session_id,
        "game_day": 1,
        "decisions": [
            {
                "document_id": doc_id,
                "agent_condition": "tier_1",
                "player_verdict": "REDACT",
                "player_correct": True,
                "latency_ms": 1500.0,
                "agreed_with_agent": False,
                "bars": {
                    "public_trust": 60,
                    "security": 20,
                    "treasury": 80,
                    "legitimacy": 70,
                    "compliance": 50,
                },
                "game_day": 1,
                "phase": 1,
                "category_tier": 1,
                "is_calibration": False,
            }
        ],
    }
    resp = await client.post("/decisions/batch", json=payload)
    assert resp.status_code == 201
    assert resp.json() == {"accepted": 1}


@pytest.mark.asyncio
async def test_batch_decisions_session_not_found(
    client: AsyncClient,
    seeded_library: list[DocumentLibrary],
) -> None:
    resp = await client.post(
        "/decisions/batch",
        json={
            "session_id": 99999,
            "game_day": 1,
            "decisions": [],
        },
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_batch_multiple_decisions(
    client: AsyncClient, seeded_library: list[DocumentLibrary]
) -> None:
    create_resp = await client.post("/sessions", json={"started_at": datetime.now(UTC).isoformat()})
    session_id = create_resp.json()["session_id"]

    decisions = [
        {
            "document_id": seeded_library[0].id,
            "agent_condition": "none",
            "player_verdict": "CLEAR",
            "player_correct": True,
            "latency_ms": 800.0,
            "agreed_with_agent": None,
            "bars": {
                "public_trust": 60,
                "security": 20,
                "treasury": 80,
                "legitimacy": 70,
                "compliance": 50,
            },
            "game_day": 1,
            "phase": 1,
            "category_tier": 1,
            "is_calibration": True,
        },
        {
            "document_id": seeded_library[1].id,
            "agent_condition": "tier_1",
            "player_verdict": "REDACT",
            "player_correct": True,
            "latency_ms": 1200.0,
            "agreed_with_agent": False,
            "bars": {
                "public_trust": 60,
                "security": 17,
                "treasury": 80,
                "legitimacy": 69,
                "compliance": 54,
            },
            "game_day": 1,
            "phase": 1,
            "category_tier": 1,
            "is_calibration": False,
        },
    ]
    resp = await client.post(
        "/decisions/batch",
        json={"session_id": session_id, "game_day": 1, "decisions": decisions},
    )
    assert resp.status_code == 201
    assert resp.json() == {"accepted": 2}
