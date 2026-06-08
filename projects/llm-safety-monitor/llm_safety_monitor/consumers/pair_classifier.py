from __future__ import annotations

import logging

import llm_safety_classifier

from llm_safety_monitor.config import Settings
from llm_safety_monitor.consumers.base import BaseConsumer, ClassifyResult

logger = logging.getLogger(__name__)


class PairSafetyClassifier(BaseConsumer):
    """Binary pair safety classifier. label=0: safe, label=1: unsafe."""

    classifier_version: str = llm_safety_classifier.get_version()

    def __init__(self, settings: Settings) -> None:
        super().__init__(mode="shadow", model_name="pair_classifier", settings=settings)

    def _load_model(self) -> None:
        path = self._settings.PAIR_CLASSIFIER_PATH
        if not path.exists():
            raise RuntimeError(f"Pair classifier checkpoint not found: {path}")
        llm_safety_classifier.load(path)
        logger.info("Pair classifier loaded from %s (version=%s)", path, self.classifier_version)

    def classify(self, text: str) -> ClassifyResult:
        predicted_label, confidence, latency_ms = llm_safety_classifier.classify_text(
            text, self._settings.PAIR_CLASSIFIER_PATH
        )
        return ClassifyResult(
            predicted_label=predicted_label,
            confidence=confidence,
            latency_ms=latency_ms,
            taxonomy_labels=None,
        )
