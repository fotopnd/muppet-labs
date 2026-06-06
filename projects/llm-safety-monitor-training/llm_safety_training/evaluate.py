from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)


@dataclass
class CalibrationBinData:
    bin_lower: float
    bin_upper: float
    count: int
    actual_positive_rate: float


@dataclass
class EvalResult:
    model_type: str
    f1: float
    precision: float
    recall: float
    per_category_f1: dict[str, float] | None
    calibration_bins: list[CalibrationBinData]
    sample_count: int
    timestamp: str


def _compute_calibration_bins(
    confidences: list[float], true_labels: list[int], n_bins: int = 10
) -> list[CalibrationBinData]:
    bins: list[CalibrationBinData] = []
    bin_size = 1.0 / n_bins
    for i in range(n_bins):
        lower = i * bin_size
        upper = (i + 1) * bin_size
        indices = [
            j
            for j, c in enumerate(confidences)
            if lower <= c < upper or (i == n_bins - 1 and c == 1.0)
        ]
        if not indices:
            continue
        count = len(indices)
        positives = sum(true_labels[j] for j in indices)
        bins.append(
            CalibrationBinData(
                bin_lower=round(lower, 2),
                bin_upper=round(upper, 2),
                count=count,
                actual_positive_rate=positives / count,
            )
        )
    return bins


def evaluate_binary(
    model_type: Literal["pair", "prompt"],
    checkpoint_path: Path,
    texts: list[str],
    labels: list[int],
) -> EvalResult:
    """Evaluate a binary classifier and return metrics + calibration bins."""
    import torch  # deferred
    from sklearn.metrics import f1_score, precision_score, recall_score  # deferred
    from transformers import AutoModelForSequenceClassification, AutoTokenizer  # deferred

    tokenizer = AutoTokenizer.from_pretrained(str(checkpoint_path))
    model = AutoModelForSequenceClassification.from_pretrained(str(checkpoint_path))
    model.eval()

    confidences: list[float] = []
    predictions: list[int] = []
    batch_size = 64

    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            enc = tokenizer(batch, truncation=True, padding=True, max_length=512, return_tensors="pt")
            logits = model(**enc).logits
            probs = torch.softmax(logits, dim=-1)[:, 1]
            preds = (probs >= 0.5).long()
            confidences.extend(probs.tolist())
            predictions.extend(preds.tolist())

    f1 = f1_score(labels, predictions, zero_division=0)
    precision = precision_score(labels, predictions, zero_division=0)
    recall = recall_score(labels, predictions, zero_division=0)
    cal_bins = _compute_calibration_bins(confidences, labels)

    return EvalResult(
        model_type=model_type,
        f1=float(f1),
        precision=float(precision),
        recall=float(recall),
        per_category_f1=None,
        calibration_bins=cal_bins,
        sample_count=len(labels),
        timestamp=datetime.now(UTC).isoformat(),
    )


def evaluate_taxonomy(
    checkpoint_path: Path,
    texts: list[str],
    labels: list[list[int]],
    category_names: tuple[str, ...],
) -> EvalResult:
    """Evaluate the multi-label taxonomy classifier."""
    import torch  # deferred
    from sklearn.metrics import f1_score  # deferred
    from transformers import AutoModelForSequenceClassification, AutoTokenizer  # deferred

    tokenizer = AutoTokenizer.from_pretrained(str(checkpoint_path))
    model = AutoModelForSequenceClassification.from_pretrained(str(checkpoint_path))
    model.eval()

    all_probs: list[list[float]] = []
    batch_size = 32

    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            enc = tokenizer(batch, truncation=True, padding=True, max_length=512, return_tensors="pt")
            logits = model(**enc).logits
            probs = torch.sigmoid(logits)
            all_probs.extend(probs.tolist())

    preds = [[1 if p >= 0.5 else 0 for p in row] for row in all_probs]

    # Per-category F1
    per_cat_f1: dict[str, float] = {}
    for i, name in enumerate(category_names):
        cat_labels = [row[i] for row in labels]
        cat_preds = [row[i] for row in preds]
        per_cat_f1[name] = float(f1_score(cat_labels, cat_preds, zero_division=0))

    macro_f1 = sum(per_cat_f1.values()) / len(per_cat_f1)

    # For calibration: use max confidence as the "overall" confidence
    max_confidences = [max(row) for row in all_probs]
    binary_labels = [1 if any(row) else 0 for row in labels]
    cal_bins = _compute_calibration_bins(max_confidences, binary_labels)

    return EvalResult(
        model_type="taxonomy",
        f1=macro_f1,
        precision=0.0,  # macro precision not computed separately
        recall=0.0,
        per_category_f1=per_cat_f1,
        calibration_bins=cal_bins,
        sample_count=len(labels),
        timestamp=datetime.now(UTC).isoformat(),
    )


def evaluate(
    model_type: Literal["pair", "prompt", "taxonomy"],
    checkpoint_path: Path,
    output_dir: Path,
) -> EvalResult:
    from llm_safety_training.datasets import (
        WILDGUARD_CATEGORIES,
        build_prompt_detector_dataset,
        load_hhrlhf_binary,
        split_wildguard,
    )

    logger.info("Evaluating %s from %s", model_type, checkpoint_path)

    if model_type == "pair":
        _, _, eval_texts, eval_labels = [], [], [], []
        # Use HH-RLHF test split + WildGuard pair eval
        _, hh_eval_labels = load_hhrlhf_binary(split="test")
        hh_eval_texts, _ = load_hhrlhf_binary(split="test")
        wg_splits = split_wildguard()
        eval_texts = hh_eval_texts[:2000] + wg_splits.pair_eval_texts
        eval_labels = hh_eval_labels[:2000] + wg_splits.pair_eval_labels
        result = evaluate_binary("pair", checkpoint_path, eval_texts, eval_labels)

    elif model_type == "prompt":
        _, _, eval_texts, eval_labels = build_prompt_detector_dataset()
        result = evaluate_binary("prompt", checkpoint_path, eval_texts, eval_labels)

    elif model_type == "taxonomy":
        wg_splits = split_wildguard()
        result = evaluate_taxonomy(
            checkpoint_path,
            wg_splits.taxonomy_eval_texts,
            wg_splits.taxonomy_eval_labels,
            WILDGUARD_CATEGORIES,
        )
    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    output_path = output_dir / f"{model_type}-{timestamp}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(asdict(result), f, indent=2)
    logger.info("Eval results written to %s", output_path)

    return result


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Evaluate a trained LLM safety classifier")
    parser.add_argument("--model", required=True, choices=["pair", "prompt", "taxonomy"])
    parser.add_argument(
        "--checkpoint",
        type=Path,
        help="Path to model checkpoint (defaults to env var per model type)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(os.getenv("EVAL_OUT", "evals")),
    )
    args = parser.parse_args()

    env_key = {"pair": "PAIR_CLASSIFIER_OUT", "prompt": "PROMPT_DETECTOR_OUT", "taxonomy": "TAXONOMY_CLASSIFIER_OUT"}
    checkpoint = args.checkpoint or Path(os.getenv(env_key[args.model], f"checkpoints/{args.model}"))

    if not checkpoint.exists():
        raise RuntimeError(f"Checkpoint not found: {checkpoint}")

    evaluate(args.model, checkpoint, args.output_dir)
