from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

from toxicity_classifier.data import get_splits, load_jigsaw, tokenise_splits
from toxicity_classifier.device import get_device

logger = logging.getLogger(__name__)

BASE_CHECKPOINT = "distilbert-base-uncased"


def train(
    data_dir: Path,
    output_dir: Path,
    epochs: int = 4,
    batch_size: int = 32,
    lr: float = 2e-5,
    max_train_samples: int | None = None,
) -> Path:
    """Fine-tune DistilBERT on Jigsaw binary toxic label. Returns path to best checkpoint."""
    import transformers
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )

    from toxicity_classifier.metrics import make_compute_metrics

    transformers.logging.set_verbosity_info()

    device_cfg = get_device()
    logger.info("Device: %s  bf16: %s", device_cfg.device, device_cfg.use_bf16)

    tokenizer = AutoTokenizer.from_pretrained(BASE_CHECKPOINT)
    model = AutoModelForSequenceClassification.from_pretrained(BASE_CHECKPOINT, num_labels=2)

    df = load_jigsaw(data_dir)
    splits = get_splits(df, max_train_samples=max_train_samples)
    splits = tokenise_splits(splits, tokenizer)

    output_dir.mkdir(parents=True, exist_ok=True)
    trainer_output = output_dir / "trainer-distilbert"
    best_dir = output_dir / "distilbert-best"

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

    training_args = TrainingArguments(
        output_dir=str(trainer_output),
        num_train_epochs=epochs,  # configurable; default 4
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=64,
        learning_rate=lr,
        warmup_steps=100,  # ~10% of a typical 1k-step epoch; stabilises early training
        weight_decay=0.01,
        eval_strategy="epoch",  # must match save_strategy for load_best_model_at_end
        save_strategy="epoch",
        load_best_model_at_end=True,  # keeps best checkpoint by metric_for_best_model
        metric_for_best_model="f1",
        greater_is_better=True,
        bf16=device_cfg.use_bf16,
        report_to="none",  # no wandb/tensorboard in portfolio build
        logging_steps=50,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=splits.train,
        eval_dataset=splits.val,
        compute_metrics=make_compute_metrics(),
        callbacks=[EpochLogCallback()],
    )

    trainer.train()

    # Save best model to a stable directory name for project 22 to load
    trainer.save_model(str(best_dir))
    tokenizer.save_pretrained(str(best_dir))
    logger.info("Best DistilBERT checkpoint saved to %s", best_dir)

    # Write epoch log
    log_path = output_dir / "distilbert-train-log.json"
    log_path.write_text(json.dumps(log_entries, indent=2))
    logger.info("Training log written to %s", log_path)

    # Clean up intermediate trainer checkpoints to save disk space
    if trainer_output.exists():
        shutil.rmtree(trainer_output)

    return best_dir
