from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

# Exact subcategory strings from allenai/wildguardmix dataset (verified 2026-06-06).
# 'benign' and 'others' are excluded — they map to all-zero label vectors.
WILDGUARD_CATEGORIES: tuple[str, ...] = (
    "causing_material_harm_by_disseminating_misinformation",
    "copyright_violations",
    "cyberattack",
    "defamation_encouraging_unethical_or_unsafe_actions",
    "disseminating_false_or_misleading_information_encouraging_disinformation_campaigns",
    "fraud_assisting_illegal_activities",
    "mental_health_over-reliance_crisis",
    "private_information_individual",
    "sensitive_information_organization_government",
    "sexual_content",
    "social_stereotypes_and_unfair_discrimination",
    "toxic_language_hate_speech",
    "violence_and_physical_harm",
)
NUM_HARM_CATEGORIES: int = len(WILDGUARD_CATEGORIES)


class SourceDataset(StrEnum):
    HH_RLHF = "hh-rlhf"
    WILDGUARD = "wildguard"
    ADVBENCH = "advbench"
    JAILBREAKBENCH = "jailbreakbench"
    LIVE = "live"
    RED_TEAM = "red_team"


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
