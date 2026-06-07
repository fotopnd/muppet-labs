from __future__ import annotations

import time

import httpx


async def chat(
    client: httpx.AsyncClient,
    model: str,
    prompt: str,
) -> tuple[str, int]:
    """
    POSTs to {OLLAMA_BASE_URL}/api/chat with stream=false.
    Returns (response_text, latency_ms).
    Raises httpx.HTTPStatusError on non-2xx.
    Raises httpx.TimeoutException on timeout (propagated to runner for logging).
    """
    start = time.monotonic()
    response = await client.post(
        "/api/chat",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
    )
    response.raise_for_status()
    latency_ms = int((time.monotonic() - start) * 1000)
    data = response.json()
    text = data["message"]["content"]
    return text, latency_ms


def make_client(base_url: str, timeout_s: int) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=base_url,
        timeout=httpx.Timeout(timeout_s),
    )
