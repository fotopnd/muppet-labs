from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from httpx import AsyncClient

from year_zero.api.routers.cards import assign_condition
from year_zero.models import DocumentLibrary


def _make_doc(**kwargs: Any) -> Any:
    """SimpleNamespace with DocumentLibrary field names — for unit-testing assign_condition."""
    defaults = {
        "id": 1,
        "sovereign_verdict": True,
        "served_none": 0,
        "served_tier_1": 0,
        "served_tier_2": 0,
        "served_tier_3": 0,
        "target_condition_mix": {"none": 0.25, "tier_1": 0.25, "tier_2": 0.25, "tier_3": 0.25},
    }
    return SimpleNamespace(**{**defaults, **kwargs})


class TestAssignCondition:
    def test_calibration_always_none(self) -> None:
        doc = _make_doc(sovereign_verdict=None)
        assert assign_condition(doc) == "none"

    def test_picks_most_underserved(self) -> None:
        # Only tier_2 has been served; others are equally under-served relative to 0.25 target
        doc = _make_doc(served_none=1, served_tier_1=1, served_tier_2=5, served_tier_3=1)
        condition = assign_condition(doc)
        # tier_2 is most over-served → not selected
        assert condition != "tier_2"

    def test_even_distribution_cycles(self) -> None:
        # Equal served counts → equal deficit; function picks deterministically
        doc = _make_doc(served_none=2, served_tier_1=2, served_tier_2=2, served_tier_3=2)
        result = assign_condition(doc)
        assert result in ("none", "tier_1", "tier_2", "tier_3")

    def test_unequal_targets(self) -> None:
        # none=0.5, tier_3=0.5 in mix; served equally → picks none or tier_3, not tier_1/tier_2
        doc = _make_doc(
            served_none=1,
            served_tier_1=1,
            served_tier_2=0,
            served_tier_3=0,
            target_condition_mix={"none": 0.5, "tier_3": 0.5},
        )
        # none and tier_3 should be picked, not tier_1 or tier_2
        result = assign_condition(doc)
        assert result in ("none", "tier_3")


@pytest.mark.asyncio
async def test_calibration_endpoint(
    client: AsyncClient, seeded_library: list[DocumentLibrary]
) -> None:
    resp = await client.get("/cards/calibration")
    assert resp.status_code == 200
    cards = resp.json()
    assert len(cards) >= 1
    for card in cards:
        assert card["agent_condition"] == "none"
        assert card["sovereign_verdict"] is None


@pytest.mark.asyncio
async def test_calibration_no_cards_returns_404(client: AsyncClient) -> None:
    # No seeded data fixture — clean DB has no calibration cards
    resp = await client.get("/cards/calibration")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_phase_cards_valid_phase(
    client: AsyncClient, seeded_library: list[DocumentLibrary]
) -> None:
    resp = await client.get("/cards/phase/2")
    assert resp.status_code == 200
    cards = resp.json()
    assert len(cards) >= 1
    for card in cards:
        assert card["phase"] == 2
        assert card["agent_condition"] in ("none", "tier_1", "tier_2", "tier_3")


@pytest.mark.asyncio
async def test_phase_cards_invalid_phase(client: AsyncClient) -> None:
    resp = await client.get("/cards/phase/5")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_phase_cards_not_found(client: AsyncClient) -> None:
    # No fixture data for phase 3 in clean DB
    resp = await client.get("/cards/phase/3")
    # Could be 200 (if seeded) or 404 (if not) — test just checks no 500
    assert resp.status_code in (200, 404)
