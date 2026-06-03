from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, PreTrainedTokenizerBase

from toxicity_classifier.data import LABEL_COLUMNS, get_splits, load_jigsaw, tokenise_splits
from toxicity_classifier.device import get_device

logger = logging.getLogger(__name__)

# Zero-shot checkpoints must match project 22's consumers exactly
ZERO_SHOT_CHECKPOINTS: dict[str, str] = {
    "distilbert": "typeform/distilbert-base-uncased-mnli",
    "roberta": "roberta-large-mnli",
}
ZERO_SHOT_CANDIDATE_LABELS = ["toxic content", "safe content"]
ZERO_SHOT_TOXIC_LABEL = "toxic content"
ZERO_SHOT_THRESHOLD = 0.5


@dataclass
class ModelMetrics:
    f1: float
    precision: float
    recall: float
    auc_roc: float
    per_category: dict[str, float]


@dataclass
class EvalResult:
    model_slug: str
    checkpoint_dir: str | None
    finetuned: ModelMetrics
    zero_shot_baseline: ModelMetrics
    evaluated_at: str
    test_size: int


def evaluate(
    checkpoint_dir: Path,
    model_key: Literal["distilbert", "roberta"],
    data_dir: Path,
    output_dir: Path = Path("eval_results"),
) -> EvalResult:
    from transformers import AutoTokenizer

    device_cfg = get_device()

    # Load fine-tuned model
    logger.info("Loading fine-tuned model from %s", checkpoint_dir)
    tokenizer = AutoTokenizer.from_pretrained(str(checkpoint_dir))
    ft_model = AutoModelForSequenceClassification.from_pretrained(str(checkpoint_dir))
    ft_model.to(device_cfg.device)
    ft_model.eval()

    # Load and tokenise — test split is the single authoritative source for texts and labels
    df = load_jigsaw(data_dir)
    splits = get_splits(df)
    splits = tokenise_splits(splits, tokenizer)
    test_ds = splits.test

    # Raw texts for zero-shot pipeline come from the same test_ds to avoid split divergence
    test_pd = test_ds.to_pandas()
    raw_texts = test_pd["comment_text"].tolist()
    raw_labels = test_ds["labels"]
    true_labels = raw_labels.tolist() if hasattr(raw_labels, "tolist") else list(raw_labels)

    # Per-category arrays from test split
    category_arrays: dict[str, list[int]] = {
        col: test_ds[col] for col in LABEL_COLUMNS if col != "toxic"
    }
    # severe_toxic etc. are int columns; convert from tensor if needed
    category_arrays = {
        k: v.tolist() if hasattr(v, "tolist") else list(v) for k, v in category_arrays.items()
    }

    # Fine-tuned predictions
    logger.info("Running fine-tuned inference on %d examples", len(raw_texts))
    ft_preds = _predict_finetuned(ft_model, tokenizer, raw_texts, device_cfg.device)

    # Zero-shot predictions (always on CPU — MPS support inconsistent across transformers versions)
    logger.info("Running zero-shot baseline (%s)", ZERO_SHOT_CHECKPOINTS[model_key])
    zs_preds = _predict_zero_shot(ZERO_SHOT_CHECKPOINTS[model_key], raw_texts)

    ft_metrics = _compute_metrics(ft_preds, true_labels, category_arrays)
    zs_metrics = _compute_metrics(zs_preds, true_labels, category_arrays)

    result = EvalResult(
        model_slug=f"{model_key}-finetuned",
        checkpoint_dir=str(checkpoint_dir),
        finetuned=ft_metrics,
        zero_shot_baseline=zs_metrics,
        evaluated_at=datetime.now(UTC).isoformat(),
        test_size=len(raw_texts),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    out_path = output_dir / f"{model_key}-finetuned-{timestamp}.json"
    out_path.write_text(json.dumps(asdict(result), indent=2))
    logger.info("Evaluation results written to %s", out_path)

    _print_summary(result)
    return result


def _predict_finetuned(
    model: AutoModelForSequenceClassification,
    tokenizer: PreTrainedTokenizerBase,
    texts: list[str],
    device: torch.device,
    batch_size: int = 64,
) -> list[int]:
    predictions: list[int] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        enc = tokenizer(batch, truncation=True, padding=True, max_length=128, return_tensors="pt")
        enc = {k: v.to(device) for k, v in enc.items()}
        with torch.no_grad():
            logits = model(**enc).logits
        preds = logits.argmax(dim=-1).cpu().tolist()
        predictions.extend(preds)
    return predictions


def _predict_zero_shot(checkpoint: str, texts: list[str], batch_size: int = 32) -> list[int]:
    from transformers import pipeline

    # Force CPU — MPS support for zero-shot classification is inconsistent
    pipe = pipeline("zero-shot-classification", model=checkpoint, device=-1)
    predictions: list[int] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        results = pipe(batch, candidate_labels=ZERO_SHOT_CANDIDATE_LABELS)
        if isinstance(results, dict):
            results = [results]
        for r in results:
            scores: dict[str, float] = dict(zip(r["labels"], r["scores"], strict=True))
            toxic_score = scores.get(ZERO_SHOT_TOXIC_LABEL, 0.0)
            predictions.append(1 if toxic_score >= ZERO_SHOT_THRESHOLD else 0)
    return predictions


def _compute_metrics(
    predictions: list[int],
    labels: list[int],
    category_arrays: dict[str, list[int]],
) -> ModelMetrics:
    from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score

    preds = np.array(predictions)
    lbls = np.array(labels)

    f1 = float(f1_score(lbls, preds, average="binary", zero_division=0))
    precision = float(precision_score(lbls, preds, average="binary", zero_division=0))
    recall = float(recall_score(lbls, preds, average="binary", zero_division=0))
    try:
        auc = float(roc_auc_score(lbls, preds))
    except ValueError:
        auc = 0.0  # roc_auc_score raises if only one class present in labels

    per_category: dict[str, float] = {}
    for col, col_labels in category_arrays.items():
        cat_lbls = np.array(col_labels)
        per_category[col] = float(np.mean(preds == cat_lbls))

    return ModelMetrics(
        f1=f1,
        precision=precision,
        recall=recall,
        auc_roc=auc,
        per_category=per_category,
    )


def _print_summary(result: EvalResult) -> None:
    ft = result.finetuned
    zs = result.zero_shot_baseline
    print(f"\n{'=' * 60}")
    print(f"Evaluation: {result.model_slug}  (n={result.test_size})")
    print(f"{'=' * 60}")
    print(f"{'Metric':<20} {'Fine-tuned':>12} {'Zero-shot':>12} {'Delta':>10}")
    print(f"{'-' * 56}")
    for metric in ("f1", "precision", "recall", "auc_roc"):
        ft_val = getattr(ft, metric)
        zs_val = getattr(zs, metric)
        print(f"{metric:<20} {ft_val:>12.4f} {zs_val:>12.4f} {ft_val - zs_val:>+10.4f}")
    print("\nPer-category accuracy (fine-tuned prediction vs label):")
    for cat, acc in ft.per_category.items():
        zs_acc = zs.per_category.get(cat, 0.0)
        print(f"  {cat:<20} ft={acc:.4f}  zs={zs_acc:.4f}  Δ={acc - zs_acc:+.4f}")
    print(f"{'=' * 60}\n")
