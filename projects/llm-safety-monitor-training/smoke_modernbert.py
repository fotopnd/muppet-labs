"""Quick MPS timing smoke test for ModernBERT-base vs RoBERTa-base.

Runs 20 training steps on synthetic data and reports step time.
No dataset download required.
"""
from __future__ import annotations

import time
import torch
from datasets import Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments

MODELS = {
    "modernbert": "answerdotai/ModernBERT-base",
    "roberta": "roberta-base",
}
N_STEPS = 20
SEQ_LEN = 128
BATCH_SIZE = 32
N_SAMPLES = BATCH_SIZE * N_STEPS + BATCH_SIZE  # enough for N_STEPS steps


def make_synthetic_dataset(tokenizer, n: int, seq_len: int) -> Dataset:
    input_ids = [[1] * seq_len] * n
    attention_mask = [[1] * seq_len] * n
    labels = [i % 2 for i in range(n)]
    return Dataset.from_dict({"input_ids": input_ids, "attention_mask": attention_mask, "labels": labels})


def smoke(model_key: str, model_name: str) -> None:
    print(f"\n{'='*60}")
    print(f"Model: {model_key} ({model_name})")
    print(f"Batch size: {BATCH_SIZE}, Steps: {N_STEPS}, Seq len: {SEQ_LEN}")

    print("  Loading tokenizer + model...")
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
    print(f"  Load time: {time.time() - t0:.1f}s  |  Params: {sum(p.numel() for p in model.parameters())/1e6:.0f}M")

    ds = make_synthetic_dataset(tokenizer, N_SAMPLES, SEQ_LEN)

    args = TrainingArguments(
        output_dir=f"/tmp/smoke-{model_key}",
        num_train_epochs=1,
        max_steps=N_STEPS,
        per_device_train_batch_size=BATCH_SIZE,
        logging_steps=5,
        report_to="none",
        save_strategy="no",
    )

    trainer = Trainer(model=model, args=args, train_dataset=ds)

    print("  Starting training...")
    t1 = time.time()
    trainer.train()
    elapsed = time.time() - t1

    secs_per_step = elapsed / N_STEPS
    print(f"\n  RESULT: {secs_per_step:.2f}s/step  ({N_STEPS} steps in {elapsed:.1f}s)")
    print(f"  Full-data estimate (pair ~80k rows, batch={BATCH_SIZE}): "
          f"~{secs_per_step * (80_000 // BATCH_SIZE) * 4 / 3600:.1f}h for 4 epochs")


if __name__ == "__main__":
    import sys
    targets = sys.argv[1:] or list(MODELS.keys())
    for key in targets:
        if key in MODELS:
            smoke(key, MODELS[key])
        else:
            print(f"Unknown model: {key}. Choose from: {list(MODELS.keys())}")
