from __future__ import annotations

from llm_safety_monitor.types import LLMInteractionEvent, SourceDataset


def test_event_schema_serialization() -> None:
    from uuid import uuid4

    event = LLMInteractionEvent(
        event_id=uuid4(),
        prompt="Is this harmful?",
        response="No, it is not.",
        source_dataset=SourceDataset.HH_RLHF,
        ground_truth_safe=True,
        ground_truth_categories=None,
    )
    serialized = event.model_dump_json()
    restored = LLMInteractionEvent.model_validate_json(serialized)
    assert restored.event_id == event.event_id
    assert restored.source_dataset == SourceDataset.HH_RLHF
    assert restored.ground_truth_safe is True


def test_event_prompt_only() -> None:
    from uuid import uuid4

    event = LLMInteractionEvent(
        event_id=uuid4(),
        prompt="How to make a bomb?",
        response=None,
        source_dataset=SourceDataset.ADVBENCH,
        ground_truth_safe=False,
    )
    assert event.response is None
    serialized = event.model_dump_json()
    restored = LLMInteractionEvent.model_validate_json(serialized)
    assert restored.response is None


def test_source_dataset_values() -> None:
    assert SourceDataset.HH_RLHF == "hh-rlhf"
    assert SourceDataset.WILDGUARD == "wildguard"
    assert SourceDataset.ADVBENCH == "advbench"
    assert SourceDataset.JAILBREAKBENCH == "jailbreakbench"
    assert SourceDataset.LIVE == "live"
