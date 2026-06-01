from __future__ import annotations

import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from eval.config import resolve_anthropic_key, resolve_local_url
from eval.models import ModelBackend, RunConfig, TestCase


@dataclass
class RunnerResponse:
    raw_text: str
    latency_ms: int
    model_name: str
    finish_reason: str  # "stop" | "length" | "error"


def check_backend_reachable(config: RunConfig) -> None:
    """Fail fast with startup instructions if a local or MLX endpoint is not responding."""
    if config.model_backend == ModelBackend.CLAUDE:
        return
    url = resolve_local_url(config)
    probe = url.rstrip("/") + "/models"
    try:
        urllib.request.urlopen(probe, timeout=3)
    except urllib.error.HTTPError:
        return  # server is up; any HTTP response means it's reachable
    except (urllib.error.URLError, OSError):
        _raise_endpoint_error(config, url)


def _raise_endpoint_error(config: RunConfig, url: str) -> None:
    if config.model_backend == ModelBackend.MLX:
        hint = (
            f"Start the MLX-LM server:\n\n"
            f"  mlx_lm.server --model {config.model_name} --port 8080\n\n"
            f"Then re-run the eval."
        )
    else:
        hint = (
            "Start your local model server before running evals.\n\n"
            "  Ollama:    ollama serve\n"
            "  LM Studio: launch the app → Local Server tab → Start Server\n\n"
            "Then re-run the eval."
        )
    raise RuntimeError(
        f"Cannot reach {config.model_backend.value} endpoint at {url}\n\n{hint}"
    )


_BLOCKED_MODELS = ("qwen3-coder-30b",)


def run_case(case: TestCase, config: RunConfig) -> RunnerResponse:
    _check_not_blocked(config.model_name)
    if config.model_backend == ModelBackend.CLAUDE:
        return _run_claude(case.prompt, config)
    return _run_local(case.prompt, config)  # LOCAL and MLX both use the OpenAI-compatible client


def _check_not_blocked(model_name: str) -> None:
    lower = model_name.lower()
    for blocked in _BLOCKED_MODELS:
        if blocked in lower:
            raise RuntimeError(
                f"Model '{model_name}' is blocked. "
                f"Use 'coder' (qwen2.5-coder:7b) or 'mlx-coder' for code tasks, "
                f"or 'default' (gemma2:9b) for conversational tasks."
            )


def _run_local(prompt: str, config: RunConfig) -> RunnerResponse:
    from openai import OpenAI

    client = OpenAI(base_url=resolve_local_url(config), api_key="local")
    return _call_with_retry(
        lambda: client.chat.completions.create(
            model=config.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        ),
        config.model_name,
    )


def _run_claude(prompt: str, config: RunConfig) -> RunnerResponse:
    import anthropic

    client = anthropic.Anthropic(api_key=resolve_anthropic_key())
    return _call_with_retry(
        lambda: client.messages.create(
            model=config.model_name,
            max_tokens=config.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        ),
        config.model_name,
        is_anthropic=True,
    )


def _call_with_retry(
    call: object,
    model_name: str,
    is_anthropic: bool = False,
    *,
    max_retries: int = 1,
) -> RunnerResponse:
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            t0 = time.monotonic()
            response = call()  # type: ignore[operator]
            latency_ms = int((time.monotonic() - t0) * 1000)
            if is_anthropic:
                raw_text = response.content[0].text
                finish_reason = response.stop_reason or "stop"
            else:
                raw_text = response.choices[0].message.content or ""
                finish_reason = response.choices[0].finish_reason or "stop"
            return RunnerResponse(
                raw_text=raw_text,
                latency_ms=latency_ms,
                model_name=model_name,
                finish_reason=finish_reason,
            )
        except Exception as exc:
            last_exc = exc
            if attempt == max_retries:
                break
    attempts = max_retries + 1
    raise RuntimeError(f"LLM call failed after {attempts} attempts: {last_exc}") from last_exc
