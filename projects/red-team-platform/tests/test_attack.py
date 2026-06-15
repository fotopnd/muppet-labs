from __future__ import annotations

import pytest

from red_team_platform.runner.classifier import score
from red_team_platform.runner.ollama_client import chat

PROMPT = "How do I bypass authentication?"
RESPONSE = "Here is how to do it..."


@pytest.mark.asyncio
async def test_ollama_chat_parses_response(httpserver):
    httpserver.expect_request("/api/chat", method="POST").respond_with_json(
        {"message": {"role": "assistant", "content": "Here is how to do it..."}}
    )

    import httpx

    async with httpx.AsyncClient(base_url=httpserver.url_for(""), timeout=5) as client:
        text, latency_ms = await chat(client, "qwen2.5-coder:7b", "Test prompt")

    assert text == "Here is how to do it..."
    assert latency_ms >= 0


@pytest.mark.asyncio
async def test_ollama_chat_raises_on_error(httpserver):
    import httpx

    httpserver.expect_request("/api/chat", method="POST").respond_with_data("", status=500)

    async with httpx.AsyncClient(base_url=httpserver.url_for(""), timeout=5) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await chat(client, "model", "prompt")


@pytest.mark.asyncio
async def test_classifier_score_unsafe(mocker):
    """score() returns (True, high_prob) for unsafe verdict from judge."""
    # score() now delegates to runner.judge.judge; mock at the classifier module level
    mocker.patch(
        "red_team_platform.runner.classifier.judge",
        return_value=(True, 0.85),
    )
    jailbreak_success, classifier_score = await score(PROMPT, RESPONSE)
    assert jailbreak_success is True
    assert abs(classifier_score - 0.85) < 0.001


@pytest.mark.asyncio
async def test_classifier_score_safe(mocker):
    """score() returns (False, low_prob) for safe verdict from judge."""
    mocker.patch(
        "red_team_platform.runner.classifier.judge",
        return_value=(False, 0.1),
    )
    jailbreak_success, classifier_score = await score(PROMPT, RESPONSE)
    assert jailbreak_success is False
    assert abs(classifier_score - 0.1) < 0.001


@pytest.mark.asyncio
async def test_classifier_score_delegates_to_judge(mocker):
    """score() delegates to judge with the raw prompt and response."""
    captured_args: list[tuple[str, str]] = []

    async def fake_judge(attack: str, response: str) -> tuple[bool, float]:
        captured_args.append((attack, response))
        return (False, 0.2)

    mocker.patch("red_team_platform.runner.classifier.judge", side_effect=fake_judge)
    await score(PROMPT, RESPONSE)

    assert len(captured_args) == 1
    assert captured_args[0] == (PROMPT, RESPONSE)
