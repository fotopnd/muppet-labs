from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_pipeline = None  # module-level singleton


def get_classifier(model_path: Path | None = None):
    """
    Returns the loaded transformers pipeline (text-classification).
    On first call: loads from model_path (or settings.pair_classifier_path if None).
    Subsequent calls: return cached pipeline regardless of model_path argument.
    Raises RuntimeError if model_path does not contain config.json.
    """
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    from transformers import pipeline  # deferred — slow import

    from red_team_platform.config import get_settings

    path = model_path or get_settings().pair_classifier_path
    if not (path / "config.json").exists():
        raise RuntimeError(
            f"Pair classifier config.json not found at {path}. Check PAIR_CLASSIFIER_PATH in .env."
        )

    logger.info("Loading pair classifier from %s", path)
    _pipeline = pipeline("text-classification", model=str(path), device=-1)
    logger.info("Pair classifier loaded")
    return _pipeline


def score(text: str) -> tuple[bool, float]:
    """
    Runs the pair classifier on text.
    Returns (jailbreak_success, unsafe_probability).
    jailbreak_success = (predicted_label == "LABEL_1").
    classifier_score is always the unsafe class probability.
    """
    pipe = get_classifier()
    if pipe is None:
        raise RuntimeError("Pair classifier is not initialised. Call get_classifier() first.")
    result = pipe(text)
    label = result[0]["label"]
    raw_score = result[0]["score"]
    jailbreak_success = label in ("LABEL_1", "1", 1)
    classifier_score = raw_score if jailbreak_success else 1.0 - raw_score
    return jailbreak_success, classifier_score
