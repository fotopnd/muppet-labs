from __future__ import annotations

import pytest

from red_team_platform.corpus.loader import AttackRecord, load_sevdeawesome


def test_load_sevdeawesome_returns_records(mocker):
    mock_ds = [
        {
            "jailbreak_prompt_text": "Attack prompt",
            "jailbreak_prompt_name": "DAN",
            "prompt_name": "Make a bomb",
        },
        {
            "jailbreak_prompt_text": "Another prompt",
            "jailbreak_prompt_name": "AIM",
            "prompt_name": "Harm someone",
        },
    ]
    mocker.patch(
        "datasets.load_dataset",
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
        {
            "jailbreak_prompt_text": "Good prompt",
            "jailbreak_prompt_name": "DAN",
            "prompt_name": "Harm",
        },
        # malformed: empty attack text
        {
            "jailbreak_prompt_text": "",
            "jailbreak_prompt_name": "DAN",
            "prompt_name": "Missing attack text",
        },
        # malformed: empty strategy
        {
            "jailbreak_prompt_text": "Another",
            "jailbreak_prompt_name": "",
            "prompt_name": "Missing strategy",
        },
    ]
    mocker.patch(
        "datasets.load_dataset",
        return_value=mock_ds,
    )

    records = load_sevdeawesome()
    assert len(records) == 1
    assert records[0].source_id == "sev-0"


@pytest.mark.xfail(
    reason="asyncpg event-loop isolation breaks on Python 3.14 + pytest-asyncio 1.x", strict=False
)
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
