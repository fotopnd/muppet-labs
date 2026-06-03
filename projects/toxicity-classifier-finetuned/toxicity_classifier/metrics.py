from __future__ import annotations

from collections.abc import Callable

import numpy as np


def make_compute_metrics() -> Callable:
    """Returns a compute_metrics function for HuggingFace Trainer (binary classification)."""
    from sklearn.metrics import f1_score

    def compute_metrics(eval_pred) -> dict[str, float]:
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        f1 = f1_score(labels, predictions, average="binary", zero_division=0)
        return {"f1": f1}

    return compute_metrics
