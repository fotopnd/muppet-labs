from __future__ import annotations

import logging
import time

from llm_safety_monitor.config import Settings
from llm_safety_monitor.consumers.base import BaseConsumer, ClassifyResult
from llm_safety_monitor.types import WILDGUARD_CATEGORIES

logger = logging.getLogger(__name__)

_THRESHOLD = 0.5


class HarmTaxonomyClassifier(BaseConsumer):
    """Multi-label harm taxonomy classifier. Returns active harm category names."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(mode="shadow", model_name="taxonomy_classifier", settings=settings)

    def _load_model(self) -> None:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer  # deferred

        path = self._settings.TAXONOMY_CLASSIFIER_PATH
        if not path.exists():
            raise RuntimeError(f"Taxonomy classifier checkpoint not found: {path}")
        self._tokenizer = AutoTokenizer.from_pretrained(str(path))
        self._model = AutoModelForSequenceClassification.from_pretrained(str(path))
        self._model.eval()
        logger.info("Taxonomy classifier loaded from %s", path)

    def classify(self, text: str) -> ClassifyResult:
        import torch  # deferred

        start = time.perf_counter()
        enc = self._tokenizer(text, truncation=True, max_length=128, return_tensors="pt")
        with torch.no_grad():
            logits = self._model(**enc).logits
        probs = torch.sigmoid(logits[0]).tolist()
        latency_ms = (time.perf_counter() - start) * 1000

        active_categories = [
            WILDGUARD_CATEGORIES[i]
            for i, p in enumerate(probs)
            if p >= _THRESHOLD and i < len(WILDGUARD_CATEGORIES)
        ]
        max_conf = max(probs) if probs else 0.0
        predicted_label = 1 if active_categories else 0

        return ClassifyResult(
            predicted_label=predicted_label,
            confidence=float(max_conf),
            latency_ms=latency_ms,
            taxonomy_labels=active_categories if active_categories else [],
        )
