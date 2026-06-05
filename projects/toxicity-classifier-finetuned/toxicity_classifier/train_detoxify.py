"""train_detoxify.py — Fine-tune bert-base-uncased with a 6-label multi-label head.

Architecture:
    bert-base-uncased → Linear(768, 6) → BCEWithLogitsLoss
    Labels: [toxic, severe_toxic, obscene, threat, insult, identity_hate]

The model is saved via save_pretrained() with num_labels=6 so it can be loaded with
AutoModelForSequenceClassification.from_pretrained(checkpoint, num_labels=6).

Consumer + seed-sim read logits[0] (toxic label) and apply sigmoid for binary classification,
keeping the interface consistent with all other dashboard models.
"""
from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

from toxicity_classifier.data import LABEL_COLUMNS, load_jigsaw
from toxicity_classifier.device import get_device

logger = logging.getLogger(__name__)

BASE_CHECKPOINT = "bert-base-uncased"
NUM_LABELS = 6


def _split_and_tokenise(df, tokenizer, max_length: int = 128, max_train_samples: int | None = None):
    """Split raw DataFrame and tokenise with all 6 label columns as FloatTensor."""
    import datasets as hf_datasets
    from sklearn.model_selection import train_test_split

    # 80/10/10 stratified on binary toxic label — same seed as data.py get_splits
    train_val, test = train_test_split(df, test_size=0.10, random_state=42, stratify=df["toxic"])
    train, val = train_test_split(
        train_val, test_size=0.1111, random_state=42, stratify=train_val["toxic"]
    )

    if max_train_samples is not None:
        train = train.iloc[:max_train_samples]

    def _make_ds(frame) -> hf_datasets.Dataset:
        keep_cols = ["comment_text"] + LABEL_COLUMNS
        ds = hf_datasets.Dataset.from_pandas(frame[keep_cols].reset_index(drop=True))

        def _tokenise(batch):
            enc = tokenizer(
                batch["comment_text"],
                truncation=True,
                padding="max_length",
                max_length=max_length,
            )
            enc["labels"] = [
                [float(batch[col][i]) for col in LABEL_COLUMNS]
                for i in range(len(batch["comment_text"]))
            ]
            return enc

        ds = ds.map(_tokenise, batched=True, remove_columns=keep_cols)
        ds.set_format("torch", columns=["input_ids", "attention_mask", "labels"])
        return ds

    return _make_ds(train), _make_ds(val), _make_ds(test)


def _make_compute_metrics():
    """Compute F1 on binary toxic label (index 0) from sigmoid of logit[0]."""
    import numpy as np
    from sklearn.metrics import f1_score

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        # logits: [n, 6]  labels: [n, 6]
        toxic_prob = 1 / (1 + np.exp(-logits[:, 0]))  # sigmoid on toxic logit
        preds = (toxic_prob >= 0.5).astype(int)
        true = labels[:, 0].astype(int)
        f1 = float(f1_score(true, preds, average="binary", zero_division=0))
        return {"f1": f1}

    return compute_metrics


def train(
    data_dir: Path,
    output_dir: Path,
    epochs: int = 3,
    batch_size: int = 32,
    lr: float = 2e-5,
    max_train_samples: int | None = None,
) -> Path:
    """Fine-tune bert-base-uncased on Jigsaw 6-label multi-label classification.

    Returns path to best checkpoint directory.
    """
    import transformers
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )

    transformers.logging.set_verbosity_info()

    device_cfg = get_device()
    logger.info("Device: %s  bf16: %s", device_cfg.device, device_cfg.use_bf16)

    tokenizer = AutoTokenizer.from_pretrained(BASE_CHECKPOINT)
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_CHECKPOINT,
        num_labels=NUM_LABELS,
        problem_type="multi_label_classification",
    )

    df = load_jigsaw(data_dir)
    train_ds, val_ds, _ = _split_and_tokenise(df, tokenizer, max_train_samples=max_train_samples)

    output_dir.mkdir(parents=True, exist_ok=True)
    trainer_output = output_dir / "trainer-detoxify"
    best_dir = output_dir / "detoxify-finetuned-best"

    log_entries: list[dict] = []

    class EpochLogCallback(transformers.TrainerCallback):
        def on_evaluate(self, args, state, control, metrics=None, **kwargs):  # noqa: B006
            if metrics:
                log_entries.append(
                    {
                        "epoch": state.epoch,
                        "train_loss": metrics.get("train_loss"),
                        "val_loss": metrics.get("eval_loss"),
                        "val_f1": metrics.get("eval_f1"),
                    }
                )

        def on_save(self, args, state, control, **kwargs):  # noqa: B006
            # MPS tensors must be flushed before safetensors write on Apple Silicon
            import torch
            if hasattr(torch, "mps") and torch.backends.mps.is_available():
                torch.mps.synchronize()

    training_args = TrainingArguments(
        output_dir=str(trainer_output),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=128,
        learning_rate=lr,
        warmup_steps=100,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        bf16=device_cfg.use_bf16,
        report_to="none",
        logging_steps=50,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        compute_metrics=_make_compute_metrics(),
        callbacks=[EpochLogCallback()],
    )

    trainer.train()

    trainer.save_model(str(best_dir))
    tokenizer.save_pretrained(str(best_dir))
    logger.info("Best detoxify-finetuned checkpoint saved to %s", best_dir)

    log_path = output_dir / "detoxify-train-log.json"
    log_path.write_text(json.dumps(log_entries, indent=2))
    logger.info("Training log written to %s", log_path)

    if trainer_output.exists():
        shutil.rmtree(trainer_output)

    return best_dir
