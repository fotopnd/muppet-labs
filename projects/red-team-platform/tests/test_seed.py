from __future__ import annotations

import pytest

from red_team_platform.corpus.loader import AttackRecord, load_sevdeawesome


def test_load_sevdeawesome_returns_records(mocker):
    mock_ds = [
        {"jailbreak_query": "Attack prompt", "strategy": "DAN", "behavior": "Make a bomb"},
        {"jailbreak_query": "Another prompt", "strategy": "AIM", "behavior": "Harm someone"},
    ]
    mocker.patch(
        "red_team_platform.corpus.loader.load_dataset",
        return_value=mock_ds,
    )

    records = load_sevdeawesome()

    assert len(records) == 2
    assert records[0].source == "sevdeawesome"
    assert records[0].source_id == "sev-0"
    assert records[0].attack_text == "Attack prompt"
    assert records[0].strategy == "DAN"
    assert records[0].harm_goal == "Make a bomb"
    assert records[0].harm_category == ""


def test_load_sevdeawesome_skips_malformed(mocker, caplog):
    mock_ds = [
        {"jailbreak_query": "Good prompt", "strategy": "DAN", "behavior": "Harm"},
        {"jailbreak_query": "", "strategy": "DAN", "behavior": "Missing attack text"},  # malformed
        {"jailbreak_query": "Another", "strategy": "", "behavior": "Missing strategy"},  # malformed
    ]
    mocker.patch(
        "red_team_platform.corpus.loader.load_dataset",
        return_value=mock_ds,
    )

    records = load_sevdeawesome()
    assert len(records) == 1
    assert records[0].source_id == "sev-0"


@pytest.mark.asyncio
async def test_seed_corpus_inserts(db_session, mocker):
    mocker.patch(
        "red_team_platform.corpus.seed.classify_category",
        return_value="toxic_language_hate_speech",
    )
    from red_team_platform.corpus.seed import seed_corpus

    records = [
        AttackRecord(
            source="sevdeawesome",
            source_id="sev-seed-test-1",
            harm_category="",
            strategy="DAN",
            attack_text="Test attack",
            harm_goal="Cause harm",
        )
    ]
    inserted, updated = await seed_corpus(db_session, records)
    assert inserted + updated == 1
