from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from error_hide_seek.agents.llm import LLMCaller
from error_hide_seek.agents.prompts import build_blue_team_prompt

log = logging.getLogger(__name__)


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
    llm: LLMCaller,
    abstract: str,
) -> AnnotateResult:
    prompt = build_blue_team_prompt(abstract)
    failures = 0

    for _ in range(3):
        raw = await llm(prompt)
        text = raw.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(l for l in lines if not l.startswith("```")).strip()
        try:
            return AnnotateResult(annotations=_parse_annotations(text), parse_failures=failures)
        except (json.JSONDecodeError, KeyError) as exc:
            log.warning("Blue team attempt failed (%s), retrying", exc)
            failures += 1

    return AnnotateResult(annotations=[], parse_failures=failures)
