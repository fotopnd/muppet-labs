from __future__ import annotations

from httpx import AsyncClient


async def test_health(api_client: AsyncClient) -> None:
    response = await api_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_stream_metrics_empty_db(api_client: AsyncClient) -> None:
    response = await api_client.get("/metrics/stream")
    assert response.status_code == 200
    data = response.json()
    assert data["event_rate_per_sec"] == 0.0
    assert data["total_events"] == 0
    assert data["category_counts"] == {}


async def test_stream_metrics_returns_event_rate(
    api_client: AsyncClient,
    seeded_classifications,
) -> None:
    response = await api_client.get("/metrics/stream")
    assert response.status_code == 200
    data = response.json()
    assert data["total_events"] == 15  # seeded_classifications inserts 15 rows


async def test_production_metrics_returns_all_models(api_client: AsyncClient) -> None:
    response = await api_client.get("/metrics/production")
    assert response.status_code == 200
    data = response.json()
    model_names = {m["model_name"] for m in data}
    assert "distilbert" in model_names
    assert "finetuned_distilbert" in model_names
    assert len(data) == 5


async def test_shadow_metrics_computed_correctly(
    api_client: AsyncClient,
    seeded_classifications,
    test_engine,
) -> None:
    # seeded_classifications: 10 shadow rows for distilbert, all predicted_label=1, 8 correct
    # → TP=8, FP=2, FN=0 → F1 = 16/18 ≈ 0.889
    response = await api_client.get("/metrics/shadow")
    assert response.status_code == 200
    data = response.json()
    distilbert = next((m for m in data if m["model_name"] == "distilbert"), None)
    assert distilbert is not None
    assert distilbert["status"] == "active"
    assert distilbert["event_count"] == 10
    assert distilbert["f1"] is not None
    assert distilbert["latency_p50"] is not None


async def test_shadow_metrics_pending_model_is_null(api_client: AsyncClient) -> None:
    response = await api_client.get("/metrics/shadow")
    assert response.status_code == 200
    data = response.json()
    finetuned = next((m for m in data if m["model_name"] == "finetuned_distilbert"), None)
    assert finetuned is not None
    assert finetuned["status"] == "pending_weights"
    assert finetuned["f1"] is None


async def test_comparison_not_found(api_client: AsyncClient) -> None:
    response = await api_client.get("/metrics/comparison/nonexistent-event-id")
    assert response.status_code == 404


async def test_anomalies_empty(api_client: AsyncClient) -> None:
    response = await api_client.get("/metrics/anomalies")
    assert response.status_code == 200
    assert response.json() == []


async def test_analytics_returns_empty_when_no_dbt(api_client: AsyncClient) -> None:
    response = await api_client.get("/metrics/analytics")
    assert response.status_code == 200
    data = response.json()
    assert data["category_trends"] == []
    assert data["model_accuracy"] == []
    assert data["escalation_rates"] == []
