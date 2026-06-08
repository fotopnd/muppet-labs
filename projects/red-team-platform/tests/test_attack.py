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


def test_classifier_score_unsafe(mocker):
    """score() returns (True, high_prob) for unsafe pair classification."""
    mocker.patch(
        "llm_safety_classifier.classify_text",
        return_value=(1, 0.85, 12.0),
    )
    jailbreak_success, classifier_score = score(PROMPT, RESPONSE)
    assert jailbreak_success is True
    assert abs(classifier_score - 0.85) < 0.001


def test_classifier_score_safe(mocker):
    """score() returns (False, low_prob) for safe pair classification."""
    mocker.patch(
        "llm_safety_classifier.classify_text",
        return_value=(0, 0.1, 8.0),
    )
    jailbreak_success, classifier_score = score(PROMPT, RESPONSE)
    assert jailbreak_success is False
    assert abs(classifier_score - 0.1) < 0.001


def test_classifier_score_uses_sep_concatenation(mocker):
    """score() passes 'prompt [SEP] response' to classify_text — not response alone."""
    captured: list[str] = []

    def fake_classify(text, model_path, **kwargs):
        captured.append(text)
        return (0, 0.2, 5.0)

    mocker.patch("llm_safety_classifier.classify_text", side_effect=fake_classify)
    score(PROMPT, RESPONSE)

    assert len(captured) == 1
    assert captured[0] == f"{PROMPT} [SEP] {RESPONSE}"
