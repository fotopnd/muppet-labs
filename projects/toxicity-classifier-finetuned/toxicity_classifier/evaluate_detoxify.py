"""evaluate_detoxify.py — Evaluate the finetuned detoxify (bert-base-uncased 6-label) checkpoint.

Loads the checkpoint produced by train_detoxify.py and evaluates on the Jigsaw test split.
Primary metric: binary toxic F1 (label index 0 from the 6-label sigmoid head).
Per-label accuracy reported for all 6 categories.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import torch

from toxicity_classifier.data import LABEL_COLUMNS, load_jigsaw
from toxicity_classifier.train_detoxify import _split_and_tokenise
from toxicity_classifier.device import get_device

logger = logging.getLogger(__name__)

_TOXIC_IDX = 0  # LABEL_COLUMNS[0] == "toxic"


@dataclass
class DetoxifyEvalResult:
    model_slug: str
    checkpoint_dir: str
    f1: float
    precision: float
    recall: float
    auc_roc: float
    per_label_accuracy: dict[str, float]
    evaluated_at: str
    test_size: int


def evaluate_detoxify(
    checkpoint_dir: Path,
    data_dir: Path,
    output_dir: Path = Path("eval_results"),
) -> DetoxifyEvalResult:
    from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    device_cfg = get_device()
    logger.info("Loading detoxify-finetuned from %s", checkpoint_dir)

    tokenizer = AutoTokenizer.from_pretrained(str(checkpoint_dir))
    model = AutoModelForSequenceClassification.from_pretrained(
        str(checkpoint_dir), num_labels=6
    )
    model.to(device_cfg.device)
    model.eval()

    import pandas as pd
    from sklearn.model_selection import train_test_split

    df = load_jigsaw(data_dir)
    # Reproduce the same 80/10/10 split used in training to avoid test leakage
    train_val, test_df = train_test_split(df, test_size=0.10, random_state=42, stratify=df["toxic"])
    test_df = test_df.reset_index(drop=True)

    raw_texts = test_df["comment_text"].tolist()
    true_labels_binary = test_df["toxic"].tolist()
    label_arrays = {col: test_df[col].tolist() for col in LABEL_COLUMNS if col != "toxic"}

    # Run inference: sigmoid on each of the 6 logits
    all_probs: list[list[float]] = []
    batch_size = 64
    for i in range(0, len(raw_texts), batch_size):
        batch = raw_texts[i : i + batch_size]
        enc = tokenizer(
            batch,
            truncation=True,
            padding=True,
            max_length=128,
            return_tensors="pt",
        )
        enc = {k: v.to(device_cfg.device) for k, v in enc.items()}
        with torch.no_grad():
            logits = model(**enc).logits  # [batch, 6]
        probs = torch.sigmoid(logits).cpu().tolist()
        all_probs.extend(probs)

    toxic_probs = [p[_TOXIC_IDX] for p in all_probs]
    toxic_preds = [1 if p >= 0.5 else 0 for p in toxic_probs]
    true_arr = np.array(true_labels_binary)
    pred_arr = np.array(toxic_preds)

    f1 = float(f1_score(true_arr, pred_arr, average="binary", zero_division=0))
    precision = float(precision_score(true_arr, pred_arr, average="binary", zero_division=0))
    recall = float(recall_score(true_arr, pred_arr, average="binary", zero_division=0))
    try:
        auc = float(roc_auc_score(true_arr, np.array(toxic_probs)))
    except ValueError:
        auc = 0.0

    per_label_accuracy: dict[str, float] = {}
    for label_idx, col in enumerate(LABEL_COLUMNS):
        if col == "toxic":
            per_label_accuracy[col] = float(np.mean(pred_arr == true_arr))
        else:
            col_true = np.array(label_arrays[col])
            col_preds = np.array([1 if p[label_idx] >= 0.5 else 0 for p in all_probs])
            per_label_accuracy[col] = float(np.mean(col_preds == col_true))

    result = DetoxifyEvalResult(
        model_slug="detoxify-finetuned",
        checkpoint_dir=str(checkpoint_dir),
        f1=f1,
        precision=precision,
        recall=recall,
        auc_roc=auc,
        per_label_accuracy=per_label_accuracy,
        evaluated_at=datetime.now(UTC).isoformat(),
        test_size=len(raw_texts),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    out_path = output_dir / f"detoxify-finetuned-{timestamp}.json"
    out_path.write_text(json.dumps(asdict(result), indent=2))
    logger.info("Eval results written to %s", out_path)

    print(f"\n{'=' * 60}")
    print(f"Evaluation: detoxify-finetuned  (n={result.test_size})")
    print(f"{'=' * 60}")
    print(f"F1:        {f1:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"AUC-ROC:   {auc:.4f}")
    print("\nPer-label accuracy (threshold=0.5):")
    for col, acc in per_label_accuracy.items():
        print(f"  {col:<20} {acc:.4f}")
    print(f"{'=' * 60}\n")

    return result
