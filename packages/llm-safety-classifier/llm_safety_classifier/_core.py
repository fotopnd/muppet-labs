from __future__ import annotations

import importlib.metadata
import time
from pathlib import Path
from typing import Any

_model_cache: dict[Path, tuple[Any, Any]] = {}


def get_version() -> str:
    try:
        return importlib.metadata.version("llm-safety-classifier")
    except importlib.metadata.PackageNotFoundError:
        return "dev"


def build_input_text(prompt: str, response: str | None) -> str:
    """Canonical [SEP] concatenation. Single source of truth for both projects."""
    if response:
        return f"{prompt} [SEP] {response}"
    return prompt


def load(model_path: Path) -> None:
    """Pre-load model without running inference. Fails fast if path is invalid."""
    _ensure_loaded(model_path)


def classify_text(
    text: str,
    model_path: Path,
    threshold: float = 0.5,
) -> tuple[int, float, float]:
    """
    Classify pre-built text against a binary sequence classifier.
    Returns (predicted_label, confidence, latency_ms).
    confidence is always the unsafe-class (label=1) probability.
    Raises RuntimeError if model_path does not contain config.json.
    """
    tokenizer, model = _ensure_loaded(model_path)

    import torch

    start = time.perf_counter()
    enc = tokenizer(text, truncation=True, max_length=128, return_tensors="pt")
    with torch.no_grad():
        logits = model(**enc).logits
    probs = torch.softmax(logits[0], dim=-1)
    confidence = float(probs[1])
    predicted_label = int(confidence >= threshold)
    latency_ms = (time.perf_counter() - start) * 1000

    return predicted_label, confidence, latency_ms


def _ensure_loaded(model_path: Path) -> tuple[Any, Any]:
    if model_path not in _model_cache:
        if not (model_path / "config.json").exists():
            raise RuntimeError(
                f"config.json not found at {model_path}. Check PAIR_CLASSIFIER_PATH in .env."
            )
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        model_obj = AutoModelForSequenceClassification.from_pretrained(str(model_path))
        model_obj.eval()
        _model_cache[model_path] = (tokenizer, model_obj)
    return _model_cache[model_path]
