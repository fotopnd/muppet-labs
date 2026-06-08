import json
from unittest.mock import AsyncMock

import pytest

from error_hide_seek.agents.blue_team import AnnotateResult, annotate
from error_hide_seek.agents.red_team import PlantResult, plant_error
from error_hide_seek.models import ErrorCategory


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
    llm = AsyncMock(return_value=response_json)
    result = await plant_error(llm, abstract, ErrorCategory.INVERTED_CONCLUSION)
    assert isinstance(result, PlantResult)
    assert result.original_text == "improves alignment by 30%"
    assert result.altered_text == "degrades alignment by 30%"


@pytest.mark.asyncio
async def test_plant_error_retries_on_bad_json():
    abstract = "We show that RLHF improves alignment by 30% on standard benchmarks."
    good_json = json.dumps(
        {
            "original_text": "improves alignment by 30%",
            "altered_text": "degrades alignment by 30%",
            "rationale": "Fixed.",
        }
    )
    llm = AsyncMock(side_effect=["not json at all", good_json])
    result = await plant_error(llm, abstract, ErrorCategory.INVERTED_CONCLUSION)
    assert result.original_text == "improves alignment by 30%"
    assert llm.call_count == 2


@pytest.mark.asyncio
async def test_plant_error_raises_on_double_failure():
    abstract = "We show that RLHF improves alignment by 30% on standard benchmarks."
    llm = AsyncMock(return_value="bad json")
    with pytest.raises((ValueError, json.JSONDecodeError, KeyError)):
        await plant_error(llm, abstract, ErrorCategory.INVERTED_CONCLUSION)


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
    llm = AsyncMock(return_value=response_json)
    result = await annotate(llm, abstract)
    assert isinstance(result, AnnotateResult)
    assert len(result.annotations) == 1
    assert result.annotations[0].text_excerpt == "improves alignment by 30%"
    assert result.annotations[0].confidence == "high"
    assert result.parse_failures == 0


@pytest.mark.asyncio
async def test_annotate_empty_list():
    response_json = json.dumps({"annotations": []})
    llm = AsyncMock(return_value=response_json)
    result = await annotate(llm, "some abstract")
    assert result.annotations == []
    assert result.parse_failures == 0


@pytest.mark.asyncio
async def test_annotate_counts_single_parse_failure():
    good_json = json.dumps(
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
    llm = AsyncMock(side_effect=["not json at all", good_json])
    result = await annotate(llm, "abstract text")
    assert len(result.annotations) == 1
    assert result.parse_failures == 1


@pytest.mark.asyncio
async def test_annotate_returns_empty_on_double_failure():
    llm = AsyncMock(return_value="bad json")
    result = await annotate(llm, "some abstract")
    assert result.annotations == []
    assert result.parse_failures == 3
