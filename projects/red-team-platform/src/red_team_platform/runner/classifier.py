from __future__ import annotations

from red_team_platform.runner.judge import judge


async def score(prompt: str, response: str) -> tuple[bool, float]:
    """Score a prompt+response pair. Delegates to the LLM judge."""
    return await judge(prompt, response)
