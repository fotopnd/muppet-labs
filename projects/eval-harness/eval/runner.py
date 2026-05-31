from __future__ import annotations

import time
from dataclasses import dataclass

from eval.config import resolve_anthropic_key, resolve_local_url
from eval.models import ModelBackend, RunConfig, TestCase


@dataclass
class RunnerResponse:
    raw_text: str
    latency_ms: int
    model_name: str
    finish_reason: str  # "stop" | "length" | "error"


def run_case(case: TestCase, config: RunConfig) -> RunnerResponse:
    if config.model_backend == ModelBackend.LOCAL:
        return _run_local(case.prompt, config)
    return _run_claude(case.prompt, config)


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
