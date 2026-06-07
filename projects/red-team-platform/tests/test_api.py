from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from red_team_platform.api.main import create_app


@pytest.fixture
def client(mocker):
    mocker.patch(
        "red_team_platform.runner.classifier.get_classifier",
        return_value=lambda text: [{"label": "LABEL_0", "score": 0.9}],
    )
    mocker.patch(
        "red_team_platform.api.main.get_classifier",
        return_value=lambda text: [{"label": "LABEL_0", "score": 0.9}],
    )
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
