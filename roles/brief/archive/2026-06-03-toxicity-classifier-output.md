# Brief Output — toxicity-classifier-finetuned

**Role:** brief
**Sequence:** `new-project-full` (step 1)
**Date:** 2026-06-03

---

## Project Name

`toxicity-classifier-finetuned`

---

## Description

A full PyTorch fine-tuning pipeline that trains DistilBERT and RoBERTa on the Jigsaw Toxic Comments dataset, evaluates both models against their zero-shot baselines, and exports production-ready checkpoint files for loading into the moderation-stream platform (project 22, Phase 2).

---

## Language(s)

- **Primary:** Python
- **ML stack:** PyTorch, HuggingFace `transformers`, `datasets`
- **Tooling:** uv, ruff, pytest

---

## Success Criteria

The project is done when all of the following are true:

1. **Data pipeline** — Jigsaw Toxic Comments dataset loads from local CSV, tokenises correctly for both DistilBERT and RoBERTa, splits into train/val/test sets with reproducible seed.
2. **Training loop — DistilBERT** — fine-tuned on Jigsaw binary toxicity label; runs to convergence on MPS (Apple Silicon) or falls back to CPU; saves best checkpoint by val F1.
3. **Training loop — RoBERTa** — same as above, separate training run, separate checkpoint.
4. **Evaluation** — both models evaluated against held-out test set; per-category breakdown reported (toxic, severe_toxic, obscene, threat, insult, identity_hate via multi-label framing or binary proxy); zero-shot baseline included for direct comparison.
5. **Checkpoint export** — two checkpoint files in a format compatible with `transformers.AutoModelForSequenceClassification.from_pretrained()` — ready to drop into project 22 config with an env var pointing to the path.
6. **Experiment doc** — markdown document summarising: zero-shot baseline vs fine-tuned F1/AUC for each model, which categories improved most, where each model still fails. This becomes part of the project README.
7. **Tests** — unit tests covering: data loading and tokenisation, model forward pass (mock weights), checkpoint save/load round-trip.
8. **Runs on local Mac (MPS or CPU)** — no GPU requirement. Colab fallback documented in README if MPS training is impractical.

---

## Constraints

- **CPU/MPS only:** no CUDA dependency; training uses `torch.device("mps")` if available, else CPU. Colab T4 is an optional fast-path, not a requirement.
- **Inference must run on CPU at 5–50ms** after export — this is the constraint from project 22 (all five models run on the VPS without GPU).
- **Freely available dataset only:** Jigsaw Toxic Comment Classification Challenge (Kaggle, free download). Dataset assumed to be downloaded locally.
- **Output is checkpoint files, not a running service:** no API, no server, no Docker. The output of this project is two directories consumable by `AutoModelForSequenceClassification.from_pretrained()`.
- **Portfolio-grade training code:** the training loop must be readable and explicit — no opaque Trainer wrappers as the only path. HuggingFace `Trainer` is acceptable if the custom loop is also present or clearly documented.

---

## Out of Scope

- Model serving / inference API (project 22 handles this)
- Fine-tuning beyond DistilBERT and RoBERTa (other models are not needed for project 22)
- Hyperparameter search / AutoML (one well-documented training run per model is sufficient)
- Multi-label classification as the primary training objective (binary toxicity label is the target; multi-label breakdown is evaluation-only)
- Any frontend or dashboard (experiment doc is a markdown file, not a Streamlit app)
- Automated Kaggle download (README documents the manual download step)

---

## Assumptions

1. **Binary classification target** — Jigsaw's `toxic` column is the primary label. The six fine-grained labels (severe_toxic, obscene, threat, insult, identity_hate) are used for evaluation breakdown only, not as training targets.
2. **HuggingFace `Trainer` + custom loop** — training uses HuggingFace `Trainer` for the main runs (faster iteration, built-in MPS support), with the training loop logic documented explicitly so it reads as first-principles.
3. **DistilBERT base:** `distilbert-base-uncased` → fine-tuned as `AutoModelForSequenceClassification` with `num_labels=2`.
4. **RoBERTa base:** `roberta-base` → fine-tuned as `AutoModelForSequenceClassification` with `num_labels=2`. (`roberta-large` excluded — memory pressure on MPS + too slow on CPU for inference.)
5. **Checkpoint format:** saved via `model.save_pretrained()` + `tokenizer.save_pretrained()` to a local directory. Project 22 loads via `from_pretrained(path)`.
6. **Jigsaw dataset path** is configured via an env var (e.g. `JIGSAW_DATA_DIR`) — not hardcoded.
7. **Project lives at** `projects/toxicity-classifier-finetuned/` — separate from moderation-stream.
8. **Colab fallback:** if MPS training is too slow (estimated >6h per model), a Colab notebook is provided that runs the same training code on T4/A100. The checkpoint is then downloaded and used locally.

---

## Handoff

**Next role:** planner
**What the planner does with this:**
- Define the full module/file structure: data loader, tokeniser, training loop, evaluation module, checkpoint manager, CLI entry points.
- Decide train/val/test split ratios and reproducibility strategy (seed, dataset version).
- Define the evaluation output format — what the experiment doc contains, how metrics are computed and stored.
- Confirm the HuggingFace `Trainer` configuration: batch size, learning rate, epochs, warmup, weight decay — or propose sensible defaults with justification.
- Confirm checkpoint naming convention that project 22 expects (planner should check project 22 config to ensure compatibility).
- Identify open questions with proposed answers (per routing.md convention).

**Flags for planner:**
- Assumption 1 (binary vs multi-label) — confirm binary is the right training objective; multi-label would require a different loss function and may produce better per-category performance.
- Assumption 3/4 (model size) — confirm `roberta-base` over `roberta-large`; the constraint is CPU inference latency at 5–50ms in project 22.
- Assumption 8 (Colab fallback) — planner should estimate training time on MPS for both models and decide whether to include a Colab notebook as a deliverable.
