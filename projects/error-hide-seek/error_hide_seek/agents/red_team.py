import json
import logging
from dataclasses import dataclass

import anthropic

from error_hide_seek.agents.prompts import build_red_team_prompt, build_red_team_retry_prompt
from error_hide_seek.models import ErrorCategory

log = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-6"


@dataclass
class PlantResult:
    original_text: str
    altered_text: str
    rationale: str


def _parse_and_validate(text: str, abstract: str) -> PlantResult:
    data = json.loads(text)
    result = PlantResult(
        original_text=data["original_text"],
        altered_text=data["altered_text"],
        rationale=data["rationale"],
    )
    if result.original_text not in abstract:
        raise ValueError("original_text not found verbatim in abstract")
    return result


async def plant_error(
    client: anthropic.AsyncAnthropic,
    abstract: str,
    category: ErrorCategory,
) -> PlantResult:
    prompt = build_red_team_prompt(abstract, category)
    msg = await client.messages.create(
        model=_MODEL,
        max_tokens=512,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text  # type: ignore[union-attr]

    try:
        return _parse_and_validate(raw, abstract)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        log.warning("Red team agent first attempt failed (%s), retrying", exc)

    retry_prompt = build_red_team_retry_prompt(abstract, category)
    msg2 = await client.messages.create(
        model=_MODEL,
        max_tokens=512,
        temperature=0.7,
        messages=[{"role": "user", "content": retry_prompt}],
    )
    raw2 = msg2.content[0].text  # type: ignore[union-attr]
    return _parse_and_validate(raw2, abstract)
