import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from error_hide_seek.agents.blue_team import AnnotateResult, annotate
from error_hide_seek.agents.red_team import PlantResult, plant_error
from error_hide_seek.models import ErrorCategory


def _make_message(text: str) -> MagicMock:
    content_block = MagicMock()
    content_block.text = text
    msg = MagicMock()
    msg.content = [content_block]
    return msg


@pytest.mark.asyncio
async def test_plant_error_success():
    abstract = "We show that RLHF improves alignment by 30% on standard benchmarks."
    response_json = json.dumps(
        {
            "original_text": "improves alignment by 30%",
            "altered_text": "degrades alignment by 30%",
            "rationale": "Inverted the direction of the improvement claim.",
        }
    )
    client = MagicMock()
    client.messages.create = AsyncMock(return_value=_make_message(response_json))
    result = await plant_error(client, abstract, ErrorCategory.INVERTED_CONCLUSION)
    assert isinstance(result, PlantResult)
    assert result.original_text == "improves alignment by 30%"
    assert result.altered_text == "degrades alignment by 30%"


@pytest.mark.asyncio
async def test_plant_error_retries_on_bad_json():
    abstract = "We show that RLHF improves alignment by 30% on standard benchmarks."
    bad_response = "not json at all"
    good_json = json.dumps(
        {
            "original_text": "improves alignment by 30%",
            "altered_text": "degrades alignment by 30%",
            "rationale": "Fixed.",
        }
    )
    client = MagicMock()
    client.messages.create = AsyncMock(
        side_effect=[_make_message(bad_response), _make_message(good_json)]
    )
    result = await plant_error(client, abstract, ErrorCategory.INVERTED_CONCLUSION)
    assert result.original_text == "improves alignment by 30%"
    assert client.messages.create.call_count == 2


@pytest.mark.asyncio
async def test_plant_error_raises_on_double_failure():
    abstract = "We show that RLHF improves alignment by 30% on standard benchmarks."
    client = MagicMock()
    client.messages.create = AsyncMock(return_value=_make_message("bad json"))
    with pytest.raises((ValueError, json.JSONDecodeError, KeyError)):
        await plant_error(client, abstract, ErrorCategory.INVERTED_CONCLUSION)


@pytest.mark.asyncio
async def test_annotate_success():
    abstract = "We show that RLHF improves alignment by 30% on standard benchmarks."
    response_json = json.dumps(
        {
            "annotations": [
                {
                    "text_excerpt": "improves alignment by 30%",
                    "confidence": "high",
                    "reason": "Suspiciously precise.",
                },
            ]
        }
    )
    client = MagicMock()
    client.messages.create = AsyncMock(return_value=_make_message(response_json))
    result = await annotate(client, abstract)
    assert isinstance(result, AnnotateResult)
    assert len(result.annotations) == 1
    assert result.annotations[0].text_excerpt == "improves alignment by 30%"
    assert result.annotations[0].confidence == "high"
    assert result.parse_failures == 0


@pytest.mark.asyncio
async def test_annotate_empty_list():
    response_json = json.dumps({"annotations": []})
    client = MagicMock()
    client.messages.create = AsyncMock(return_value=_make_message(response_json))
    result = await annotate(client, "some abstract")
    assert result.annotations == []
    assert result.parse_failures == 0


@pytest.mark.asyncio
async def test_annotate_counts_single_parse_failure():
    """First attempt fails, second succeeds → parse_failures=1."""
    bad_msg = _make_message("not json at all")
    good_msg = _make_message(
        json.dumps(
            {
                "annotations": [
                    {
                        "text_excerpt": "suspicious claim here",
                        "confidence": "medium",
                        "reason": "Unusual phrasing.",
                    }
                ]
            }
        )
    )
    client = MagicMock()
    client.messages.create = AsyncMock(side_effect=[bad_msg, good_msg])
    result = await annotate(client, "abstract text")
    assert len(result.annotations) == 1
    assert result.parse_failures == 1


@pytest.mark.asyncio
async def test_annotate_returns_empty_on_double_failure():
    client = MagicMock()
    client.messages.create = AsyncMock(return_value=_make_message("bad json"))
    result = await annotate(client, "some abstract")
    assert result.annotations == []
    assert result.parse_failures == 2
