from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from llm_safety_monitor.api.models import ClassificationResult, Interaction


async def _seed_events(db_session, n: int = 10) -> list[Interaction]:
    """Seed n interactions with known ground truth and matching classifications."""
    interactions = []
    for i in range(n):
        interaction = Interaction(
            id=uuid4(),
            prompt_text=f"Test prompt {i}",
            response_text=f"Test response {i}",
            source_dataset="hh-rlhf",
            ground_truth_safe=(i % 2 == 0),  # alternating safe/unsafe
            ground_truth_categories=None,
            created_at=datetime.now(UTC),
        )
        db_session.add(interaction)
        interactions.append(interaction)
    await db_session.commit()

    for interaction in interactions:
        pair_clf = ClassificationResult(
            model_name="pair_classifier",
            content=interaction.prompt_text[:500],
            predicted_label=1 if not interaction.ground_truth_safe else 0,
            confidence=0.9,
            latency_ms=10.0,
            event_id=interaction.id,
            taxonomy_labels=None,
        )
        db_session.add(pair_clf)
    await db_session.commit()

    return interactions


async def test_health(api_client) -> None:
    resp = await api_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_metrics_empty(api_client) -> None:
    resp = await api_client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data


async def test_metrics_with_seeded_data(api_client, db_session) -> None:
    await _seed_events(db_session, n=10)
    resp = await api_client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    models = data["models"]
    assert len(models) >= 1
    pair_model = next((m for m in models if m["model_name"] == "pair_classifier"), None)
    assert pair_model is not None
    assert pair_model["sample_count"] >= 10
    # With perfect predictions, F1 should be > 0
    assert pair_model["f1"] > 0.0
    assert 0.0 <= pair_model["precision"] <= 1.0
    assert 0.0 <= pair_model["recall"] <= 1.0


async def test_calibration_empty(api_client) -> None:
    resp = await api_client.get("/metrics/calibration")
    assert resp.status_code == 200
    assert "models" in resp.json()


async def test_stream_recent_empty(api_client) -> None:
    resp = await api_client.get("/stream/recent")
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data


async def test_stream_recent_with_data(api_client, db_session) -> None:
    interactions = await _seed_events(db_session, n=3)
    resp = await api_client.get("/stream/recent?limit=5")
    assert resp.status_code == 200
    events = resp.json()["events"]
    assert len(events) >= 3
    for event in events:
        assert "event_id" in event
        assert "prompt_text" in event
        assert "verdicts" in event
        assert "source_dataset" in event


async def test_disagreements_empty(api_client) -> None:
    resp = await api_client.get("/metrics/disagreements")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "samples" in data


async def test_cases_empty(api_client) -> None:
    resp = await api_client.get("/cases")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "samples" in data


async def test_cases_with_escalated_data(api_client, db_session) -> None:
    from uuid import uuid4
    from llm_safety_monitor.api.models import ClassificationResult, Interaction

    interaction = Interaction(
        id=uuid4(),
        prompt_text="How do I make explosives?",
        response_text="Here is how...",
        source_dataset="wildguard",
        ground_truth_safe=False,
        escalated=True,
        escalation_reason="JAILBREAK",
    )
    db_session.add(interaction)
    await db_session.commit()

    pair_clf = ClassificationResult(
        model_name="pair_classifier",
        content=interaction.prompt_text[:500],
        predicted_label=1,
        confidence=0.95,
        latency_ms=12.0,
        event_id=interaction.id,
        taxonomy_labels=None,
    )
    db_session.add(pair_clf)
    await db_session.commit()

    resp = await api_client.get("/cases")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    sample = next((s for s in data["samples"] if str(interaction.id) == s["event_id"]), None)
    assert sample is not None
    assert sample["escalation_reason"] == "JAILBREAK"


async def test_disagreements_with_seeded_data(api_client, db_session) -> None:
    from uuid import uuid4
    from llm_safety_monitor.api.models import ClassificationResult, Interaction

    interaction = Interaction(
        id=uuid4(),
        prompt_text="Violent content prompt",
        response_text=None,
        source_dataset="wildguard",
        ground_truth_safe=False,
    )
    db_session.add(interaction)
    await db_session.commit()

    # pair says safe (0), taxonomy flags a category — disagreement
    pair_clf = ClassificationResult(
        model_name="pair_classifier",
        content=interaction.prompt_text[:500],
        predicted_label=0,
        confidence=0.4,
        latency_ms=10.0,
        event_id=interaction.id,
        taxonomy_labels=None,
    )
    tax_clf = ClassificationResult(
        model_name="taxonomy_classifier",
        content=interaction.prompt_text[:500],
        predicted_label=1,
        confidence=0.8,
        latency_ms=15.0,
        event_id=interaction.id,
        taxonomy_labels=["violence_and_physical_harm"],
    )
    db_session.add(pair_clf)
    db_session.add(tax_clf)
    await db_session.commit()

    resp = await api_client.get("/metrics/disagreements")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    sample = next((s for s in data["samples"] if str(interaction.id) == s["event_id"]), None)
    assert sample is not None
    assert sample["pair_label"] == 0
    assert "violence_and_physical_harm" in sample["taxonomy_labels"]
