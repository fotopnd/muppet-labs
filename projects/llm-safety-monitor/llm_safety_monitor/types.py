from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

# Verify these names against the WildGuard dataset schema before training.
# See llm_safety_training/datasets.py for inspection instructions.
WILDGUARD_CATEGORIES: tuple[str, ...] = (
    "Violent Crimes",
    "Non-Violent Crimes",
    "Sex-Related Crimes",
    "Child Sexual Exploitation",
    "Specialized Advice",
    "Privacy",
    "Intellectual Property",
    "Indiscriminate Weapons",
    "Hate",
    "Self-Harm",
    "Sexual Content",
    "Elections",
    "Disinformation",
)
NUM_HARM_CATEGORIES: int = len(WILDGUARD_CATEGORIES)


class SourceDataset(StrEnum):
    HH_RLHF = "hh-rlhf"
    WILDGUARD = "wildguard"
    ADVBENCH = "advbench"
    JAILBREAKBENCH = "jailbreakbench"
    LIVE = "live"


class EscalationReason(StrEnum):
    JAILBREAK = "JAILBREAK"
    BENIGN_HARMFUL = "BENIGN_HARMFUL"
    LOG_ONLY = "LOG_ONLY"
    MODEL_DISAGREEMENT = "MODEL_DISAGREEMENT"
    ADVERSARIAL_PROMPT_FLAGGED = "ADVERSARIAL_PROMPT_FLAGGED"


class LLMInteractionEvent(BaseModel):
    event_id: UUID
    prompt: str
    response: str | None = None
    source_dataset: SourceDataset
    ground_truth_safe: bool | None = None
    ground_truth_categories: list[str] | None = None
