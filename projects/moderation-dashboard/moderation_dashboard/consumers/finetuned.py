from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

from moderation_dashboard.consumers.base import BaseConsumer

logger = logging.getLogger(__name__)

# HuggingFace Trainer default labels or project-8 export names
_POSITIVE_LABELS = {"LABEL_1", "toxic", "1"}


class FinetunedConsumer(BaseConsumer):
    def __init__(
        self,
        model_name: str,
        group_id: str,
        mode: Literal["production", "shadow"],
        bootstrap_servers: str,
        topic: str,
        db_url: str,
        checkpoint_path: Path,
    ) -> None:
        super().__init__(model_name, group_id, mode, bootstrap_servers, topic, db_url)
        from transformers import pipeline

        logger.info("Loading fine-tuned model from %s...", checkpoint_path)
        self._pipe = pipeline(
            "text-classification",
            model=str(checkpoint_path),
            device=-1,
        )
        logger.info("Fine-tuned model ready.")

    def classify(self, content: str) -> tuple[int, float]:
        if self._pipe is None:
            raise RuntimeError(f"{self.model_name} weights not loaded")
        result = self._pipe(content[:512])
        item = result[0] if isinstance(result, list) else result
        label: str = item["label"]
        score: float = float(item["score"])
        predicted = 1 if label in _POSITIVE_LABELS else 0
        # score is the model's confidence for its predicted label
        return predicted, score


class FinetunedDistilBertConsumer(FinetunedConsumer):
    pass
