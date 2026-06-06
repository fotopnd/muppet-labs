from __future__ import annotations

import logging
import time

import torch

from llm_safety_monitor.config import Settings
from llm_safety_monitor.consumers.base import BaseConsumer, ClassifyResult
from llm_safety_monitor.types import LLMInteractionEvent

logger = logging.getLogger(__name__)


class PromptAdversarialDetector(BaseConsumer):
    """Binary prompt adversarial detector. label=0: benign, label=1: adversarial."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(mode="shadow", model_name="prompt_detector", settings=settings)

    def _load_model(self) -> None:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer  # deferred

        path = self._settings.PROMPT_DETECTOR_PATH
        if not path.exists():
            raise RuntimeError(f"Prompt detector checkpoint not found: {path}")
        self._tokenizer = AutoTokenizer.from_pretrained(str(path))
        self._model = AutoModelForSequenceClassification.from_pretrained(str(path))
        self._model.eval()
        logger.info("Prompt detector loaded from %s", path)

    def _build_input_text(self, event: LLMInteractionEvent) -> str:
        return event.prompt

    def classify(self, text: str) -> ClassifyResult:
        start = time.perf_counter()
        enc = self._tokenizer(text, truncation=True, max_length=512, return_tensors="pt")
        with torch.no_grad():
            logits = self._model(**enc).logits
        probs = torch.softmax(logits[0], dim=-1)
        confidence = float(probs[1])
        predicted_label = int(confidence >= 0.5)
        latency_ms = (time.perf_counter() - start) * 1000

        return ClassifyResult(
            predicted_label=predicted_label,
            confidence=confidence,
            latency_ms=latency_ms,
            taxonomy_labels=None,
        )
