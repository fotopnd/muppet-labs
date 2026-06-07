import json
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from error_hide_seek.models import Experiment, ExperimentPaper, Paper, PlantedError


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
