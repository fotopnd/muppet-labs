from __future__ import annotations

import logging
from typing import Literal

from moderation_dashboard.consumers.base import BaseConsumer

logger = logging.getLogger(__name__)

_CANDIDATE_LABELS = ["toxic content", "safe content"]
_TOXIC_LABEL = "toxic content"


class RobertaZeroShotConsumer(BaseConsumer):
    def __init__(
        self,
        model_name: str,
        group_id: str,
        mode: Literal["production", "shadow"],
        bootstrap_servers: str,
        topic: str,
        db_url: str,
    ) -> None:
        super().__init__(model_name, group_id, mode, bootstrap_servers, topic, db_url)
        from transformers import pipeline

        logger.info("Loading RoBERTa zero-shot model...")
        self._pipe = pipeline(
            "zero-shot-classification",
            model="roberta-large-mnli",
            device=-1,
        )
        logger.info("RoBERTa zero-shot ready.")

    def classify(self, content: str) -> tuple[int, float]:
        result = self._pipe(content[:512], candidate_labels=_CANDIDATE_LABELS)
        scores: dict[str, float] = dict(zip(result["labels"], result["scores"], strict=True))
        confidence = scores.get(_TOXIC_LABEL, 0.0)
        return (1 if confidence >= 0.5 else 0), confidence
