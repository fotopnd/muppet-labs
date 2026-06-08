from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from red_team_platform.api.main import create_app
from red_team_platform.models import Attack, Run, RunSession


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_attacks_empty(client: TestClient) -> None:
    response = client.get("/attacks")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 0


def test_list_sessions_empty(client: TestClient) -> None:
    response = client.get("/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_clusters_empty(client: TestClient) -> None:
    response = client.get("/clusters")
    assert response.status_code == 200
    assert "summaries" in response.json()


def test_cluster_members_404(client: TestClient) -> None:
    response = client.get("/clusters/9999/members")
    assert response.status_code == 404


def test_sample_404(client: TestClient) -> None:
    import uuid

    response = client.get(f"/sample/{uuid.uuid4()}")
    assert response.status_code == 404


def test_coverage_empty(client: TestClient) -> None:
    response = client.get("/coverage")
    assert response.status_code == 200
    data = response.json()
    assert "cells" in data


def test_strategy_comparison_empty(client: TestClient) -> None:
    response = client.get("/strategy-comparison")
    assert response.status_code == 200
    assert "bars" in response.json()


def test_regression_empty(client: TestClient) -> None:
    response = client.get("/regression")
    assert response.status_code == 200
    data = response.json()
    assert "points" in data
    assert "model_names" in data


# --- Aggregation correctness tests (require live test DB) ---


@pytest.mark.xfail(reason="asyncpg event-loop isolation breaks on Python 3.14 + pytest-asyncio 1.x", strict=False)
@pytest.mark.asyncio
async def test_strategy_comparison_computes_asr(db_session):
    """Verifies the strategy-comparison endpoint computes asr correctly from seeded data."""
    import uuid

    from red_team_platform.api.routers.strategy import get_strategy_comparison

    # Seed: 1 attack with strategy "DAN", 2 runs — 1 success, 1 failure
    atk = Attack(
        source="test",
        source_id=f"agg-test-{uuid.uuid4()}",
        harm_category="violence_and_physical_harm",
        strategy="DAN",
        attack_text="Aggregation test prompt",
    )
    db_session.add(atk)
    await db_session.flush()

    sess = RunSession(model_name="test-model", total_attacks=2, total_successes=1, asr=0.5)
    db_session.add(sess)
    await db_session.flush()

    run_success = Run(
        session_id=sess.id,
        attack_id=atk.id,
        model_name="test-model",
        response_text="Jailbroken",
        jailbreak_success=True,
        classifier_score=0.9,
        latency_ms=300,
    )
    run_fail = Run(
        session_id=sess.id,
        attack_id=atk.id,
        model_name="test-model",
        response_text="Safe",
        jailbreak_success=False,
        classifier_score=0.1,
        latency_ms=200,
    )
    db_session.add(run_success)
    db_session.add(run_fail)
    await db_session.flush()

    result = await get_strategy_comparison(db=db_session)

    dan_bar = next((b for b in result.bars if b.strategy == "DAN"), None)
    assert dan_bar is not None
    assert dan_bar.total_runs >= 2
    assert dan_bar.total_successes >= 1
    assert abs(dan_bar.asr - dan_bar.total_successes / dan_bar.total_runs) < 0.001
