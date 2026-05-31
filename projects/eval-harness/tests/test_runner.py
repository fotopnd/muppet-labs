from __future__ import annotations

import pytest
from pytest_httpserver import HTTPServer

from eval.models import DatasetSource, ModelBackend, RunConfig, TestCase
from eval.runner import run_case


def _config(base_url: str) -> RunConfig:
    url = f"{base_url}/v1"
    return RunConfig(
        model_backend=ModelBackend.LOCAL,
        model_name="test-model",
        endpoint_url=url,
        dataset_names=[DatasetSource.CUSTOM],
        rubric_names=[],
        max_tokens=64,
        temperature=0.0,
    )


def _case() -> TestCase:
    return TestCase(
        id="custom:runner-test",
        prompt="Say hello.",
        dataset=DatasetSource.CUSTOM,
    )


def _openai_response(content: str) -> dict:
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1000000,
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
    }


def test_run_case_local_success(httpserver: HTTPServer):
    httpserver.expect_request("/v1/chat/completions", method="POST").respond_with_json(
        _openai_response("Hello there!")
    )
    config = _config(httpserver.url_for(""))
    response = run_case(_case(), config)
    assert response.raw_text == "Hello there!"
    assert response.finish_reason == "stop"
    assert response.latency_ms >= 0


def test_run_case_local_returns_latency(httpserver: HTTPServer):
    httpserver.expect_request("/v1/chat/completions", method="POST").respond_with_json(
        _openai_response("response")
    )
    config = _config(httpserver.url_for(""))
    response = run_case(_case(), config)
    assert isinstance(response.latency_ms, int)
    assert response.latency_ms >= 0


def test_run_case_local_http_error(httpserver: HTTPServer):
    httpserver.expect_request("/v1/chat/completions", method="POST").respond_with_data(
        "Internal Server Error", status=500, content_type="text/plain"
    )
    config = _config(httpserver.url_for(""))
    with pytest.raises(RuntimeError, match="LLM call failed"):
        run_case(_case(), config)
