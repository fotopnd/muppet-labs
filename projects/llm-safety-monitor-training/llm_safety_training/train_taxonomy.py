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
    batch_size: int = 64,
    seed: int = 42,
) -> None:
    """Train DistilBERT multi-label harm taxonomy classifier on WildGuard 30% allocation."""
    from datasets import Dataset  # deferred: slow import
    from transformers import (  # deferred: slow import
        AutoModelForSequenceClassification,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )

    from llm_safety_training.datasets import NUM_HARM_CATEGORIES, split_wildguard

    logger.info("Loading WildGuard taxonomy split...")
    wg_splits = split_wildguard(seed=seed)
    logger.info(
        "Train: %d examples, Eval: %d examples",
        len(wg_splits.taxonomy_train_texts),
        len(wg_splits.taxonomy_eval_texts),
    )

    model_name = "microsoft/deberta-v3-base"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, num_labels=NUM_HARM_CATEGORIES
    )
    # problem_type="multi_label_classification" switches loss to BCEWithLogitsLoss
    model.config.problem_type = "multi_label_classification"

    def tokenize(texts: list[str], labels: list[list[int]]) -> Dataset:
        enc = tokenizer(texts, truncation=True, padding=True, max_length=512)
        # BCEWithLogitsLoss expects float labels
        float_labels = [[float(v) for v in row] for row in labels]
        return Dataset.from_dict({**enc, "labels": float_labels})

    train_ds = tokenize(wg_splits.taxonomy_train_texts, wg_splits.taxonomy_train_labels)
    eval_ds = tokenize(wg_splits.taxonomy_eval_texts, wg_splits.taxonomy_eval_labels)

    args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=32,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        warmup_steps=200,
        seed=seed,
        logging_steps=50,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
    )
    trainer.train()
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    logger.info("Taxonomy classifier (deberta-v3-base) saved to %s", output_dir)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Train harm taxonomy classifier")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            os.getenv(
                "TAXONOMY_CLASSIFIER_OUT",
                f"checkpoints/taxonomy-classifier-{datetime.now(UTC).strftime('%Y-%m-%d')}",
            )
        ),
    )
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    train(args.output_dir, epochs=args.epochs, batch_size=args.batch_size, seed=args.seed)
