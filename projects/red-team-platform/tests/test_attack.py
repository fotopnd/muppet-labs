from __future__ import annotations

import pytest

from red_team_platform.runner.classifier import score
from red_team_platform.runner.ollama_client import chat


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


def test_classifier_score_label1(mocker):
    mocker.patch(
        "red_team_platform.runner.classifier.get_classifier",
        return_value=lambda text: [{"label": "LABEL_1", "score": 0.85}],
    )
    jailbreak_success, classifier_score = score("malicious text")
    assert jailbreak_success is True
    assert abs(classifier_score - 0.85) < 0.001


def test_classifier_score_label0(mocker):
    mocker.patch(
        "red_team_platform.runner.classifier.get_classifier",
        return_value=lambda text: [{"label": "LABEL_0", "score": 0.9}],
    )
    jailbreak_success, classifier_score = score("safe text")
    assert jailbreak_success is False
    assert abs(classifier_score - 0.1) < 0.001
