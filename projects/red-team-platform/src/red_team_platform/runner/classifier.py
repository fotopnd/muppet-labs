from __future__ import annotations

import logging

import llm_safety_classifier

logger = logging.getLogger(__name__)


def score(prompt: str, response: str) -> tuple[bool, float]:
    """
    Scores a prompt+response pair using the shared pair classifier.
    Returns (jailbreak_success, unsafe_probability).
    Input text is constructed with the canonical [SEP] concatenation.
    """
    from red_team_platform.config import get_settings

    settings = get_settings()
    text = llm_safety_classifier.build_input_text(prompt, response)
    predicted_label, confidence, _ = llm_safety_classifier.classify_text(
        text, settings.pair_classifier_path
    )
    return bool(predicted_label), confidence


def warm_up(model_path=None) -> None:
    """Pre-load the classifier so the first attack doesn't pay the load cost."""
    from red_team_platform.config import get_settings

    path = model_path or get_settings().pair_classifier_path
    llm_safety_classifier.load(path)
    logger.info(
        "Pair classifier warm-up complete (version=%s)", llm_safety_classifier.get_version()
    )
