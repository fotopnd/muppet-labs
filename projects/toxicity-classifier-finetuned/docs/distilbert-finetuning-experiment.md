# Fine-Tuning DistilBERT for Toxicity Classification: Experiment and Results

## Overview

Fine-tuning DistilBERT (Distilled Bidirectional Encoder Representations from Transformers) on 127,000 labelled examples raises toxicity classification F1 from 0.32 to 0.85 over a zero-shot baseline, with precision improving from 0.21 to 0.83. This document covers the training configuration decisions, the overfitting behaviour observed across epochs, and how the resulting checkpoint integrates into a Kafka-based moderation event stream without code changes at the consumer.

---

## Problem / Motivation

The moderation stream (project 22) was initially built with zero-shot classification using HuggingFace pipelines for both DistilBERT and RoBERTa (Robustly Optimized BERT Pretraining Approach). Zero-shot inference requires no labelled data and is fast to deploy, which made it a reasonable choice for Phase 1 validation of the pipeline architecture.

The evaluation results tell a different story. The zero-shot DistilBERT baseline on the Jigsaw test set (15,958 examples) achieves F1 of 0.32 and precision of 0.21. In a moderation context, precision measures the fraction of flagged content that is genuinely toxic. At 0.21, roughly four in five flags would be false positives, producing unacceptable reviewer burden and eroding trust in the system. Recall at 0.74 shows the baseline does identify most toxic content, though at the cost of indiscriminate flagging.

The core problem is that zero-shot classification is solving the wrong task. The MNLI (Multi-Genre Natural Language Inference) checkpoint used for zero-shot inference was trained to recognise entailment between sentences, and adapting it to binary toxicity detection via candidate label matching is a crude proxy. Fine-tuning on labelled toxicity data is the direct solution.

---

## Design Decisions

**Binary label over multi-label.** The Jigsaw dataset includes six toxicity categories (toxic, severe toxic, obscene, threat, insult, identity hate). The fine-tuned model is trained on the binary `toxic` label only. This decision prioritises the production use case: the moderation stream needs a reliable triage signal, not a full taxonomy. Multi-label classification would require a more complex output head, per-label threshold tuning, and substantially more labelled data per category (the minority categories have very few positive examples). The per-category accuracy figures in the evaluation confirm that the binary classifier generalises well across categories (0.90 to 0.95 range), which validates the single-label approach for the current pipeline stage.

**`load_best_model_at_end=True` with epoch-level evaluation.** Training is configured to evaluate at the end of each epoch and restore the best checkpoint by validation F1 at the end of training. The epoch log demonstrates why this matters:

| Epoch | Val Loss | Val F1   |
|-------|---------|----------|
| 1     | 0.0804  | 0.8276   |
| 2     | 0.0821  | **0.8349** |
| 3     | 0.0922  | 0.8211   |
| 4     | 0.1060  | 0.8270   |

The model peaks at epoch 2. From epoch 3 onward, validation loss rises while training loss continues to fall, indicating overfitting. Without `load_best_model_at_end`, the exported checkpoint would be the epoch 4 model (the last epoch) rather than epoch 2, which is measurably worse on both loss and F1. The performance difference is modest here, though the pattern would likely be more pronounced on a smaller dataset or with more epochs.

**Zero-shot baseline runs on CPU.** The evaluation script runs the zero-shot pipeline with `device=-1` (CPU), even when MPS (Metal Performance Shaders, Apple Silicon's GPU framework) is available. This is deliberate: MPS support for zero-shot classification pipelines in current HuggingFace versions is inconsistent, producing occasional silent correctness failures rather than explicit errors. CPU inference is slower (approximately 15 to 20 minutes for the test set) though it is reproducible and produces verifiable results. The fine-tuned inference pass runs on MPS with no issues.

**`bf16=False` on MPS.** The training script disables bfloat16 on MPS regardless of hardware. MPS bf16 support in Transformers 5.x is inconsistent across model architectures and can produce silent gradient corruption. The performance cost of float32 on Apple Silicon is acceptable given the training time (approximately 3.5 hours for 4 epochs on 127,000 training examples on an M4 chip with 24 GB unified memory).

**Env-var-driven activation for the downstream consumer.** The fine-tuned checkpoint is designed to be loaded by the moderation stream without code changes. Setting `DISTILBERT_CHECKPOINT_PATH` in the consuming project's `.env` file causes the model registry to switch the consumer from zero-shot to fine-tuned inference. The checkpoint directory is stored at `resources/models/toxicity-classifier-finetuned/distilbert-best/` in the workspace, separate from the training project, so it can be referenced by multiple consuming projects without path duplication.

---

## Architecture

The training pipeline exposes two CLI entry points (`uv run train`, `uv run evaluate`). The evaluate command runs two passes on the held-out test split: fine-tuned inference on MPS, then zero-shot baseline on CPU using the same texts and labels, producing a side-by-side metrics table and a JSON result file.

Data flows as follows: the Jigsaw CSV is loaded and split into train (80%), validation (10%), and test (10%) sets with a fixed random seed for reproducibility. The tokeniser maps raw text to input IDs with a 128-token maximum length and padding. The Trainer handles batching, gradient accumulation, and checkpoint management. After training completes, the best checkpoint is copied to a stable directory name (`distilbert-best`) independent of Trainer's internal epoch numbering, and intermediate checkpoints are deleted to avoid multi-gigabyte disk accumulation.

The moderation stream consumer (`FinetunedDistilBertConsumer`) reads the checkpoint path from settings at startup. When the env var is set, the consumer status in the stream dashboard switches from `pending_weights` to `active`, and the consumer begins classifying events with the fine-tuned model. The checkpoint directory contains the standard HuggingFace artefacts (`model.safetensors`, `tokenizer.json`, `config.json`, `tokenizer_config.json`) and is compatible with `AutoModelForSequenceClassification.from_pretrained()` without modification.

---

## Implementation Details

**Epoch log callback.** The Trainer does not expose per-epoch validation metrics in a structured format by default. A custom `EpochLogCallback` intercepts the `on_evaluate` event and appends val loss and val F1 to an in-memory list, which is serialised to `distilbert-train-log.json` after training completes. This gives a clean epoch-by-epoch view of convergence that is independent of Trainer's internal log format, which changes between HuggingFace versions.

**`train_loss` is null in the epoch log.** The training loss is available in Trainer's log history at `logging_steps` intervals, though it is not directly accessible in the `on_evaluate` callback without traversing the state history. For this experiment the val loss and F1 are sufficient to diagnose overfitting, so the missing train loss field was left as null rather than introducing a more complex callback. A future iteration could aggregate the training loss over the epoch for a complete convergence picture.

**`pin_memory` warning.** MPS does not support pinned memory for the DataLoader. Trainer enables `pin_memory=True` by default, which produces a UserWarning on every training run. This is a Trainer-level default that cannot be overridden via `TrainingArguments` in the current API without subclassing. The warning is cosmetic and does not affect training correctness.

---

## Results / Validation

Evaluation on the held-out test set (15,958 examples):

| Metric     | Fine-tuned | Zero-shot | Delta    |
|------------|-----------|-----------|----------|
| F1         | 0.8473    | 0.3223    | +0.5250  |
| Precision  | 0.8282    | 0.2056    | +0.6226  |
| Recall     | 0.8672    | 0.7449    | +0.1223  |
| AUC-ROC    | 0.9241    | 0.7200    | +0.2041  |

Per-category accuracy of the fine-tuned model against each Jigsaw sub-label:

| Category      | Fine-tuned | Zero-shot |
|---------------|-----------|-----------|
| severe_toxic  | 0.9090    | 0.6600    |
| obscene       | 0.9487    | 0.6855    |
| threat        | 0.9023    | 0.6552    |
| insult        | 0.9460    | 0.6844    |
| identity_hate | 0.9083    | 0.6579    |

The AUC-ROC (Area Under the Receiver Operating Characteristic Curve) of 0.924 is the most informative single number for a production deployment: it measures ranking quality across all decision thresholds, not just at the 0.5 default. A score of 0.924 means the classifier correctly ranks a random toxic comment above a random non-toxic comment 92.4% of the time, which provides meaningful headroom for threshold tuning to trade precision against recall depending on reviewer capacity.

---

## Limitations and Future Work

**Binary label only.** The fine-tuned model predicts toxic or not toxic. The per-category accuracy figures show it generalises well to sub-labels as a side effect, though it is not calibrated for category-specific decisions. A production system requiring category-level routing (e.g. threat escalation vs. general moderation) would need per-category classifiers or a multi-label head.

**Single training run.** No hyperparameter search was conducted. The learning rate (2e-5), warmup steps (100), and weight decay (0.01) are standard defaults from the HuggingFace fine-tuning literature. A systematic search over learning rate and batch size would likely yield further improvement, though the F1 of 0.85 on a binary task with a realistic class imbalance (~10% positive rate) is already a competitive baseline.

**No threshold tuning.** All metrics are reported at the default 0.5 decision threshold. For a moderation pipeline with a known reviewer capacity, the optimal threshold is lower (higher recall, accepting more false positives for human review) or higher (higher precision, routing only high-confidence cases). The AUC-ROC of 0.924 provides the flexibility to set this threshold post-deployment.

**RoBERTa in progress.** A parallel fine-tuning run for RoBERTa-base is underway. The comparison between the two models will determine which checkpoint is deployed as the primary classifier in the moderation stream. Results will be added to the evaluation directory when the run completes.

---

## Conclusion

Fine-tuning a DistilBERT classifier on 127,000 labelled examples closes the gap between zero-shot inference and production-grade toxicity detection: precision rises from 0.21 to 0.83, eliminating the false positive burden that made zero-shot deployment impractical. The training pipeline is designed around reproducibility and clean checkpoint management, with epoch-level overfitting detection and env-var-driven activation in the downstream consumer. The result is a model that is not only measurably better by the numbers but is architecturally integrated into a live stream processing system without requiring code changes to deploy.
