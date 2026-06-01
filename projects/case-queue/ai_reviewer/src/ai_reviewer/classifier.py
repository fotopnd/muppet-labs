from __future__ import annotations

import json

import anthropic
import httpx

from ai_reviewer.models import Action, CaseDetail, ClassificationResult

_SYSTEM_PROMPT = """\
You are an expert trust and safety analyst. You review content that has been flagged for
potential policy violations and decide whether to take action.

For each case you receive, respond with a JSON object (and nothing else) in this exact format:
{
  "action": "approve" | "reject" | "escalate",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<one sentence explaining your decision>"
}

Definitions:
- approve: The content clearly violates policy and should be removed/actioned.
- reject: The content does not violate policy (false positive). No action needed.
- escalate: The case is ambiguous or high-stakes and requires human senior review.

Use "escalate" when you are uncertain, when content is borderline, or when the potential
harm of a wrong decision is high (e.g., threats, identity hate with low context).\
"""

_USER_TEMPLATE = """\
Case ID: {case_id}
Category: {category}
Severity: {severity}
Source: {source}

Content to review:
---
{content}
---\
"""


def _build_user_message(case: CaseDetail) -> str:
    return _USER_TEMPLATE.format(
        case_id=case.id,
        category=case.category.replace("_", " "),
        severity=case.severity,
        source=case.source,
        content=case.content,
    )


def _strip_fences(text: str) -> str:
    """Remove markdown code fences that some models wrap JSON in."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        # drop opening fence line (```json or ```) and closing ```
        inner = lines[1:] if len(lines) > 1 else lines
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        stripped = "\n".join(inner).strip()
    return stripped


def _parse_llm_response(raw: str, confidence_threshold: float) -> ClassificationResult:
    try:
        data = json.loads(_strip_fences(raw))
        action = Action(data["action"])
        confidence = float(data["confidence"])
        reasoning = str(data.get("reasoning", "No reasoning provided."))
    except (json.JSONDecodeError, KeyError, ValueError):
        return ClassificationResult(
            action=Action.escalate,
            confidence=0.0,
            reasoning=f"LLM response could not be parsed — escalating. Raw: {raw[:200]}",
        )

    if confidence < confidence_threshold and action != Action.escalate:
        note = f"Confidence {confidence:.0%} below threshold — escalated. Original: {reasoning}"
        return ClassificationResult(
            action=Action.escalate,
            confidence=confidence,
            reasoning=note,
        )

    return ClassificationResult(action=action, confidence=confidence, reasoning=reasoning)


async def classify_with_claude(
    case: CaseDetail,
    model: str,
    confidence_threshold: float,
) -> ClassificationResult:
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=model,
        max_tokens=256,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_message(case)}],
    )
    raw = message.content[0].text if message.content else ""
    return _parse_llm_response(raw, confidence_threshold)


async def classify_with_ollama(
    case: CaseDetail,
    base_url: str,
    model: str,
    confidence_threshold: float,
) -> ClassificationResult:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_message(case)},
        ],
        "temperature": 0.1,
        "stream": False,
    }
    async with httpx.AsyncClient() as http:
        resp = await http.post(
            f"{base_url}/chat/completions",
            json=payload,
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()
        raw = data["choices"][0]["message"]["content"]
    return _parse_llm_response(raw, confidence_threshold)
