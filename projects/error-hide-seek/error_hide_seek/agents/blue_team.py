import json
import logging
from dataclasses import dataclass

import anthropic

from error_hide_seek.agents.prompts import build_blue_team_prompt

log = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-6"


@dataclass
class Annotation:
    text_excerpt: str
    confidence: str
    reason: str


@dataclass
class AnnotateResult:
    annotations: list[Annotation]
    parse_failures: int


def _parse_annotations(text: str) -> list[Annotation]:
    data = json.loads(text)
    return [
        Annotation(
            text_excerpt=a["text_excerpt"],
            confidence=a["confidence"],
            reason=a["reason"],
        )
        for a in data.get("annotations", [])
    ]


async def annotate(
    client: anthropic.AsyncAnthropic,
    abstract: str,
) -> AnnotateResult:
    prompt = build_blue_team_prompt(abstract)
    failures = 0

    msg = await client.messages.create(
        model=_MODEL,
        max_tokens=1024,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text  # type: ignore[union-attr]

    try:
        return AnnotateResult(annotations=_parse_annotations(raw), parse_failures=failures)
    except (json.JSONDecodeError, KeyError) as exc:
        log.warning("Blue team agent first attempt failed (%s), retrying", exc)
        failures += 1

    msg2 = await client.messages.create(
        model=_MODEL,
        max_tokens=1024,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
    raw2 = msg2.content[0].text  # type: ignore[union-attr]
    try:
        return AnnotateResult(annotations=_parse_annotations(raw2), parse_failures=failures)
    except (json.JSONDecodeError, KeyError) as exc2:
        log.warning("Blue team agent second attempt failed (%s), returning empty list", exc2)
        failures += 1
        return AnnotateResult(annotations=[], parse_failures=failures)
