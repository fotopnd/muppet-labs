from __future__ import annotations

import uuid

import pytest

from red_team_platform.cluster.kmeans import ClusterResult, ClusterSummaryResult, cluster_failures


def make_rows(n: int) -> list[dict]:
    categories = ["toxic_language_hate_speech", "violence_and_physical_harm", "cyberattack"]
    strategies = ["DAN", "AIM", "UCAR"]
    return [
        {
            "run_id": uuid.uuid4(),
            "attack_text": f"Attack text number {i} with some content to vectorize",
            "harm_category": categories[i % len(categories)],
            "strategy": strategies[i % len(strategies)],
            "classifier_score": 0.8 + (i % 10) * 0.01,
        }
        for i in range(n)
    ]


def test_cluster_failures_returns_correct_types():
    rows = make_rows(20)
    results, summaries = cluster_failures(rows, k=3)

    assert all(isinstance(r, ClusterResult) for r in results)
    assert all(isinstance(s, ClusterSummaryResult) for s in summaries)
    assert len(summaries) == 3
    assert sum(s.size for s in summaries) == 20


def test_cluster_failures_raises_on_insufficient_rows():
    rows = make_rows(5)
    with pytest.raises(ValueError, match="Not enough failures"):
        cluster_failures(rows, k=8)


def test_cluster_failures_representative_is_in_cluster():
    rows = make_rows(30)
    results, summaries = cluster_failures(rows, k=3)

    for summary in summaries:
        cluster_texts = {r.attack_text for r in results if r.cluster_id == summary.cluster_id}
        assert summary.representative_text in cluster_texts


def test_cluster_failures_all_rows_assigned():
    rows = make_rows(24)
    results, _ = cluster_failures(rows, k=4)
    assert len(results) == 24
    assigned_run_ids = {r.run_id for r in results}
    original_run_ids = {str(r["run_id"]) for r in rows}
    assert assigned_run_ids == original_run_ids
