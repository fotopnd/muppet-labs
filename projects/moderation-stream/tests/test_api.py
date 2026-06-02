from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(api_client: AsyncClient) -> None:
    response = await api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_metrics_returns_five_models(api_client: AsyncClient) -> None:
    response = await api_client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert len(data["models"]) == 5


@pytest.mark.asyncio
async def test_metrics_all_model_names_present(api_client: AsyncClient) -> None:
    response = await api_client.get("/metrics")
    names = {m["model_name"] for m in response.json()["models"]}
    expected = {
        "distilbert-zero-shot",
        "roberta-zero-shot",
        "detoxify",
        "distilbert-finetuned",
        "roberta-finetuned",
    }
    assert names == expected


@pytest.mark.asyncio
async def test_metrics_phase2_pending_when_no_checkpoint(api_client: AsyncClient) -> None:
    response = await api_client.get("/metrics")
    ft_models = [m for m in response.json()["models"] if "finetuned" in m["model_name"]]
    for m in ft_models:
        assert m["status"] == "pending_weights"


@pytest.mark.asyncio
async def test_metrics_phase1_active(api_client: AsyncClient) -> None:
    response = await api_client.get("/metrics")
    phase1 = [
        m for m in response.json()["models"]
        if m["model_name"] in ("distilbert-zero-shot", "roberta-zero-shot", "detoxify")
    ]
    for m in phase1:
        assert m["status"] == "active"


@pytest.mark.asyncio
async def test_metrics_has_generated_at(api_client: AsyncClient) -> None:
    response = await api_client.get("/metrics")
    assert "generated_at" in response.json()


@pytest.mark.asyncio
async def test_metrics_computes_accuracy_and_latency(
    api_client: AsyncClient,
    seeded_results: list,
) -> None:
    """Verify that /metrics aggregates real rows correctly.

    seeded_results inserts 10 rows for distilbert-zero-shot:
    - latencies 10–100 ms  →  p50 = 55.0 ms
    - 8 correct, 2 wrong   →  accuracy = 0.8
    """
    response = await api_client.get("/metrics")
    assert response.status_code == 200
    by_name = {m["model_name"]: m for m in response.json()["models"]}
    m = by_name["distilbert-zero-shot"]
    assert m["total_processed"] == 10
    assert m["correct"] == 8
    assert m["accuracy"] == pytest.approx(0.8, abs=1e-3)
    assert m["p50_latency_ms"] == pytest.approx(55.0, abs=0.5)
    assert m["throughput_cps"] > 0
