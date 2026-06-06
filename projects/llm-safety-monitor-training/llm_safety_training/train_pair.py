from __future__ import annotations

import argparse
import logging
import os
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def train(
    output_dir: Path,
    epochs: int = 4,
    batch_size: int = 128,
    seed: int = 42,
    max_train_samples: int | None = None,
) -> None:
    """Train DeBERTa-v3-small binary pair safety classifier on HH-RLHF + WildGuard."""
    import random  # deferred
    from datasets import Dataset  # deferred: slow import
    from transformers import (  # deferred: slow import
        AutoModelForSequenceClassification,
        AutoTokenizer,
        Trainer,
        TrainerCallback,
        TrainingArguments,
    )

    from llm_safety_training.datasets import load_hhrlhf_binary, split_wildguard

    logger.info("Loading datasets...")
    hh_texts, hh_labels = load_hhrlhf_binary(split="train")
    wg_splits = split_wildguard(seed=seed)

    train_texts = hh_texts + wg_splits.pair_train_texts
    train_labels = hh_labels + wg_splits.pair_train_labels
    eval_texts = wg_splits.pair_eval_texts
    eval_labels = wg_splits.pair_eval_labels

    if max_train_samples is not None and max_train_samples < len(train_texts):
        rng = random.Random(seed)
        indices = rng.sample(range(len(train_texts)), max_train_samples)
        train_texts = [train_texts[i] for i in indices]
        train_labels = [train_labels[i] for i in indices]

    logger.info("Train: %d examples, Eval: %d examples", len(train_texts), len(eval_texts))

    model_name = "microsoft/deberta-v3-small"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

    def tokenize(texts: list[str], labels: list[int]) -> Dataset:
        enc = tokenizer(texts, truncation=True, padding=True, max_length=512)
        return Dataset.from_dict({**enc, "labels": labels})

    train_ds = tokenize(train_texts, train_labels)
    eval_ds = tokenize(eval_texts, eval_labels)

    import json  # deferred

    class EpochLogCallback(TrainerCallback):
        def __init__(self, log_path: Path) -> None:
            self._log_path = log_path
            self._log: list[dict] = []

        def on_evaluate(self, args, state, control, metrics=None, **kwargs):
            self._log.append({
                "epoch": state.epoch,
                "train_loss": round(state.log_history[-1].get("loss", 0.0), 4) if state.log_history else None,
                "val_loss": round(metrics.get("eval_loss", 0.0), 4) if metrics else None,
            })
            self._log_path.write_text(json.dumps(self._log, indent=2))

    args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=64,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        warmup_steps=500,
        seed=seed,
        logging_steps=100,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        callbacks=[EpochLogCallback(output_dir / "epoch_log.json")],
    )
    trainer.train()
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    logger.info("Pair classifier (deberta-v3-small) saved to %s", output_dir)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Train pair safety classifier")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            os.getenv(
                "PAIR_CLASSIFIER_OUT",
                f"checkpoints/pair-classifier-{datetime.now(UTC).strftime('%Y-%m-%d')}",
            )
        ),
    )
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-train-samples", type=int, default=None)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    train(args.output_dir, epochs=args.epochs, batch_size=args.batch_size, seed=args.seed, max_train_samples=args.max_train_samples)
