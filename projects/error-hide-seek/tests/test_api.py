import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from error_hide_seek.api.routers.experiments import _assign_conditions_and_categories
from error_hide_seek.models import CATEGORY_CYCLE, Experiment, ExperimentPaper, Paper, PlantedError


def _make_claude_message(payload: dict) -> MagicMock:
    block = MagicMock()
    block.text = json.dumps(payload)
    msg = MagicMock()
    msg.content = [block]
    return msg


@pytest_asyncio.fixture
async def seed_paper(db_session: AsyncSession) -> Paper:
    paper = Paper(
        arxiv_id="2401.99999",
        title="Test Safety Paper",
        abstract=(
            "We demonstrate that our method improves alignment by 30% "
            "on the standard safety benchmark suite."
        ),
        categories="cs.AI",
    )
    db_session.add(paper)
    await db_session.flush()
    return paper


@pytest_asyncio.fixture
async def seed_experiment(db_session: AsyncSession, seed_paper: Paper) -> Experiment:
    exp = Experiment(name="Test Experiment", description="For testing")
    db_session.add(exp)
    await db_session.flush()
    ep = ExperimentPaper(experiment_id=exp.id, paper_id=seed_paper.id, condition="unaided")
    db_session.add(ep)
    await db_session.flush()
    return exp


@pytest_asyncio.fixture
async def seed_planted_error(
    db_session: AsyncSession, seed_paper: Paper, seed_experiment: Experiment
) -> PlantedError:
    abstract = seed_paper.abstract
    original = "improves alignment by 30%"
    altered = "degrades alignment by 30%"
    pe = PlantedError(
        paper_id=seed_paper.id,
        experiment_id=seed_experiment.id,
        category="inverted_conclusion",
        original_text=original,
        altered_text=altered,
        altered_abstract=abstract.replace(original, altered, 1),
        rationale="Inverted direction.",
    )
    db_session.add(pe)
    await db_session.flush()
    return pe


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_list_papers_empty(client: AsyncClient):
    r = await client.get("/papers")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_paper_not_found(client: AsyncClient):
    r = await client.get("/papers/99999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_paper(client: AsyncClient, seed_paper: Paper):
    r = await client.get(f"/papers/{seed_paper.id}")
    assert r.status_code == 200
    assert r.json()["arxiv_id"] == "2401.99999"


@pytest.mark.asyncio
async def test_create_experiment(client: AsyncClient, seed_paper: Paper):
    r = await client.post(
        "/experiments",
        json={"name": "Exp Alpha", "description": "desc", "paper_ids": [seed_paper.id]},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Exp Alpha"
    assert len(data["papers"]) == 1
    assert data["papers"][0]["condition"] in ("unaided", "agent_only", "human_agent")


@pytest.mark.asyncio
async def test_create_session_unaided(
    client: AsyncClient,
    seed_experiment: Experiment,
    seed_paper: Paper,
    seed_planted_error: PlantedError,
):
    r = await client.post(
        "/sessions",
        json={"experiment_id": seed_experiment.id, "paper_id": seed_paper.id},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["condition"] == "unaided"
    assert data["status"] == "open"
    assert "degrades alignment by 30%" in data["abstract_text"]
    assert data["annotations"] == []
    assert data["scored_result"] is None
    return data["session_id"]


@pytest.mark.asyncio
async def test_submit_review(
    client: AsyncClient,
    seed_experiment: Experiment,
    seed_paper: Paper,
    seed_planted_error: PlantedError,
):
    # Create session first
    r = await client.post(
        "/sessions",
        json={"experiment_id": seed_experiment.id, "paper_id": seed_paper.id},
    )
    session_id = r.json()["session_id"]

    # Submit review with a true positive detection
    r = await client.post(
        "/reviews",
        json={
            "session_id": session_id,
            "detections": [
                {"text_excerpt": "degrades alignment by 30%", "note": "seems wrong"},
            ],
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_submit_review_double_submit(
    client: AsyncClient,
    seed_experiment: Experiment,
    seed_paper: Paper,
    seed_planted_error: PlantedError,
):
    r = await client.post(
        "/sessions",
        json={"experiment_id": seed_experiment.id, "paper_id": seed_paper.id},
    )
    session_id = r.json()["session_id"]

    await client.post(
        "/reviews",
        json={"session_id": session_id, "detections": []},
    )
    r2 = await client.post(
        "/reviews",
        json={"session_id": session_id, "detections": []},
    )
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_get_results(
    client: AsyncClient,
    seed_experiment: Experiment,
):
    r = await client.get(f"/results/{seed_experiment.id}")
    assert r.status_code == 200
    data = r.json()
    assert data["experiment_id"] == seed_experiment.id
    assert "conditions" in data
    assert len(data["conditions"]) == 3


@pytest.mark.asyncio
async def test_create_session_unaided_sets_agent_skipped(
    client: AsyncClient,
    seed_experiment: Experiment,
    seed_paper: Paper,
    seed_planted_error: PlantedError,
):
    r = await client.post(
        "/sessions",
        json={"experiment_id": seed_experiment.id, "paper_id": seed_paper.id},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["agent_run_status"] == "skipped"
    assert data["parse_failures"] == 0


def _make_annotate_result(annotations_payload: list[dict], parse_failures: int = 0) -> MagicMock:
    from error_hide_seek.agents.blue_team import Annotation, AnnotateResult

    annotations = [
        Annotation(
            text_excerpt=a["text_excerpt"],
            confidence=a["confidence"],
            reason=a.get("reason", ""),
        )
        for a in annotations_payload
    ]
    return AnnotateResult(annotations=annotations, parse_failures=parse_failures)


@pytest.mark.asyncio
async def test_agent_only_filters_low_confidence(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_paper: Paper,
):
    """AGENT_ONLY: low-confidence annotations are excluded from auto-scoring."""
    exp = Experiment(name="LowConfTest", description="")
    db_session.add(exp)
    await db_session.flush()

    ep = ExperimentPaper(
        experiment_id=exp.id,
        paper_id=seed_paper.id,
        condition="agent_only",
        intended_category="inverted_conclusion",
    )
    db_session.add(ep)

    original = "improves alignment by 30%"
    altered = "degrades alignment by 30%"
    pe = PlantedError(
        paper_id=seed_paper.id,
        experiment_id=exp.id,
        category="inverted_conclusion",
        original_text=original,
        altered_text=altered,
        altered_abstract=seed_paper.abstract.replace(original, altered, 1),
        rationale="Inverted.",
    )
    db_session.add(pe)
    await db_session.commit()

    # High-confidence excerpt overlaps with original_text → TP.
    # Low-confidence excerpt is a false alarm that should be excluded.
    ann_result = _make_annotate_result(
        [
            {"text_excerpt": "alignment by 30%", "confidence": "high", "reason": "r"},
            {"text_excerpt": "standard safety benchmark suite", "confidence": "low", "reason": "r"},
        ]
    )

    with patch("error_hide_seek.api.routers.sessions.annotate", AsyncMock(return_value=ann_result)):
        r = await client.post(
            "/sessions",
            json={"experiment_id": exp.id, "paper_id": seed_paper.id},
        )

    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "completed"
    assert data["agent_run_status"] == "success"
    # Only the high-confidence annotation was counted — TP was found
    assert data["scored_result"]["true_positives"] == 1
    # Low-confidence annotation was excluded — no false positive from it
    assert data["scored_result"]["false_positives"] == 0


@pytest.mark.asyncio
async def test_agent_only_parse_failure_recorded(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_paper: Paper,
):
    """AGENT_ONLY: parse failures from annotate() are stored on the session."""
    exp = Experiment(name="ParseFailTest", description="")
    db_session.add(exp)
    await db_session.flush()

    ep = ExperimentPaper(
        experiment_id=exp.id,
        paper_id=seed_paper.id,
        condition="agent_only",
        intended_category="number_substitution",
    )
    db_session.add(ep)

    original = "improves alignment by 30%"
    altered = "degrades alignment by 30%"
    pe = PlantedError(
        paper_id=seed_paper.id,
        experiment_id=exp.id,
        category="number_substitution",
        original_text=original,
        altered_text=altered,
        altered_abstract=seed_paper.abstract.replace(original, altered, 1),
        rationale="Number change.",
    )
    db_session.add(pe)
    await db_session.commit()

    # Simulate both attempts failing — empty annotations, 2 parse failures
    from error_hide_seek.agents.blue_team import AnnotateResult
    ann_result = AnnotateResult(annotations=[], parse_failures=2)

    with patch("error_hide_seek.api.routers.sessions.annotate", AsyncMock(return_value=ann_result)):
        r = await client.post(
            "/sessions",
            json={"experiment_id": exp.id, "paper_id": seed_paper.id},
        )

    assert r.status_code == 201
    data = r.json()
    assert data["agent_run_status"] == "parse_failed"
    assert data["parse_failures"] == 2


# ---------------------------------------------------------------------------
# Stratified assignment unit tests
# ---------------------------------------------------------------------------


def test_assign_conditions_same_seed_is_deterministic():
    """Same paper_ids + experiment_id always produce the same assignment."""
    paper_ids = list(range(1, 10))
    result1 = _assign_conditions_and_categories(paper_ids, experiment_id=42)
    result2 = _assign_conditions_and_categories(paper_ids, experiment_id=42)
    assert result1 == result2


def test_assign_conditions_different_seeds_differ():
    """Different experiment_ids produce different shuffles."""
    paper_ids = list(range(1, 10))
    result1 = _assign_conditions_and_categories(paper_ids, experiment_id=1)
    result2 = _assign_conditions_and_categories(paper_ids, experiment_id=2)
    # With high probability the shuffled order differs
    assert [p for p, _, _ in result1] != [p for p, _, _ in result2]


def test_assign_conditions_all_paper_ids_present():
    paper_ids = [10, 20, 30, 40, 50]
    result = _assign_conditions_and_categories(paper_ids, experiment_id=7)
    assert sorted(p for p, _, _ in result) == sorted(paper_ids)


def test_assign_conditions_categories_are_valid():
    paper_ids = list(range(1, 16))
    result = _assign_conditions_and_categories(paper_ids, experiment_id=99)
    for _, _, cat in result:
        assert cat in CATEGORY_CYCLE


def test_assign_conditions_three_conditions_present():
    paper_ids = list(range(1, 10))  # 9 papers → 3 each
    result = _assign_conditions_and_categories(paper_ids, experiment_id=5)
    conditions = [c for _, c, _ in result]
    assert "unaided" in conditions
    assert "agent_only" in conditions
    assert "human_agent" in conditions


@pytest.mark.asyncio
async def test_detection_min_length_enforced(
    client: AsyncClient,
    seed_experiment: Experiment,
    seed_paper: Paper,
    seed_planted_error: PlantedError,
):
    r = await client.post(
        "/sessions",
        json={"experiment_id": seed_experiment.id, "paper_id": seed_paper.id},
    )
    session_id = r.json()["session_id"]

    r = await client.post(
        "/reviews",
        json={
            "session_id": session_id,
            "detections": [{"text_excerpt": "short", "note": None}],
        },
    )
    assert r.status_code == 422
