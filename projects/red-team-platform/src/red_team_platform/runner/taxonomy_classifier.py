from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_pipeline = None  # module-level singleton


def get_taxonomy_classifier(model_path: Path | None = None):
    """
    Returns the loaded transformers pipeline (text-classification, top_k=1).
    On first call: loads from model_path (or settings.taxonomy_classifier_path if None).
    Subsequent calls: return cached pipeline regardless of model_path argument.
    Raises RuntimeError if model_path does not contain config.json.
    """
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    from transformers import pipeline  # deferred — slow import

    from red_team_platform.config import get_settings

    path = model_path or get_settings().taxonomy_classifier_path
    if not (path / "config.json").exists():
        raise RuntimeError(
            f"Taxonomy classifier config.json not found at {path}. "
            "Check TAXONOMY_CLASSIFIER_PATH in .env."
        )

    logger.info("Loading taxonomy classifier from %s", path)
    _pipeline = pipeline("text-classification", model=str(path), device=-1, top_k=1)
    logger.info("Taxonomy classifier loaded")
    return _pipeline


def classify_category(text: str) -> str:
    """
    Runs the taxonomy classifier on text.
    Returns the top-scoring category label string (e.g. "toxic_language_hate_speech").
    Raises RuntimeError if classifier not initialised.
    """
    pipe = get_taxonomy_classifier()
    if pipe is None:
        raise RuntimeError(
            "Taxonomy classifier is not initialised. Call get_taxonomy_classifier() first."
        )
    result = pipe(text)
    # top_k=1 returns [[{"label": "...", "score": float}]]
    return result[0][0]["label"]
