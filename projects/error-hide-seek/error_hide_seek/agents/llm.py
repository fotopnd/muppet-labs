from __future__ import annotations

from collections.abc import Awaitable, Callable

import httpx

from error_hide_seek.config import settings

LLMCaller = Callable[[str], Awaitable[str]]


def make_caller(max_tokens: int = 512, temperature: float = 0.7) -> LLMCaller:
    if settings.anthropic_api_key:
        import anthropic

        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        async def _anthropic(prompt: str) -> str:
            msg = await _client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text  # type: ignore[union-attr]

        return _anthropic

    async def _ollama(prompt: str) -> str:
        async with httpx.AsyncClient(timeout=120.0) as http:
            resp = await http.post(
                f"{settings.ollama_base_url}/v1/chat/completions",
                json={
                    "model": settings.ollama_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    return _ollama
