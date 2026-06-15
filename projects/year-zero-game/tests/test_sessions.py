from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_session(client: AsyncClient) -> None:
    resp = await client.post("/sessions", json={"started_at": datetime.now(UTC).isoformat()})
    assert resp.status_code == 201
    data = resp.json()
    assert "session_id" in data
    assert isinstance(data["session_id"], int)


@pytest.mark.asyncio
async def test_patch_session(client: AsyncClient) -> None:
    # Create first
    create_resp = await client.post("/sessions", json={"started_at": datetime.now(UTC).isoformat()})
    session_id = create_resp.json()["session_id"]

    patch_payload = {
        "ended_at": datetime.now(UTC).isoformat(),
        "total_days": 3,
        "total_decisions": 30,
        "correct_decisions": 22,
        "accuracy": 0.733,
        "phase_reached": 2,
        "game_over_condition": "TRUST_ZERO",
        "final_bars": {
            "public_trust": 0,
            "security": 45,
            "treasury": 60,
            "legitimacy": 55,
            "compliance": 50,
        },
        "compliance_profile": {
            "total_agreements": 18,
            "total_overrides": 7,
            "total_no_agent_decisions": 5,
            "agreement_rate": 0.72,
            "correct_agreements": 15,
            "correct_overrides": 5,
            "correct_no_agent": 2,
        },
        "calibration_accuracy": 0.8,
        "calibration_decisions": 10,
        "category_tiers": {"violence": 2, "hate_speech": 1},
    }
    resp = await client.patch(f"/sessions/{session_id}", json=patch_payload)
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


@pytest.mark.asyncio
async def test_patch_session_not_found(client: AsyncClient) -> None:
    resp = await client.patch(
        "/sessions/99999",
        json={
            "ended_at": datetime.now(UTC).isoformat(),
            "total_days": 1,
            "total_decisions": 10,
            "correct_decisions": 5,
            "accuracy": 0.5,
            "phase_reached": 1,
            "game_over_condition": "TREASURY_ZERO",
            "final_bars": {
                "public_trust": 50,
                "security": 50,
                "treasury": 0,
                "legitimacy": 50,
                "compliance": 50,
            },
            "compliance_profile": {},
            "calibration_accuracy": 0.5,
            "calibration_decisions": 10,
            "category_tiers": {},
        },
    )
    assert resp.status_code == 404
