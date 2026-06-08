from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from error_hide_seek.agents.llm import LLMCaller
from error_hide_seek.agents.prompts import build_red_team_prompt, build_red_team_retry_prompt
from error_hide_seek.models import ErrorCategory

log = logging.getLogger(__name__)


@dataclass
class PlantResult:
    original_text: str
    altered_text: str
    rationale: str


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        inner = [l for l in lines if not l.startswith("```")]
        text = "\n".join(inner).strip()
    return text


def _parse_and_validate(text: str, abstract: str) -> PlantResult:
    data = json.loads(_extract_json(text))
    result = PlantResult(
        original_text=data["original_text"],
        altered_text=data["altered_text"],
        rationale=data["rationale"],
    )
    if result.original_text not in abstract:
        raise ValueError("original_text not found verbatim in abstract")
    return result


async def plant_error(
    llm: LLMCaller,
    abstract: str,
    category: ErrorCategory,
) -> PlantResult:
    prompt = build_red_team_prompt(abstract, category)
    raw = await llm(prompt)

    for attempt in range(3):
        if attempt == 0:
            prompt = build_red_team_prompt(abstract, category)
        else:
            prompt = build_red_team_retry_prompt(abstract, category)
        raw = await llm(prompt)
        try:
            return _parse_and_validate(raw, abstract)
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            log.warning("Red team attempt %d failed (%s)%s", attempt + 1, exc, ", retrying" if attempt < 2 else "")

    raise ValueError("Red team agent failed after 3 attempts")
