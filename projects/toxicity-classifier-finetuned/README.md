# toxicity-classifier-finetuned

Fine-tuning pipeline for DistilBERT and RoBERTa on the Jigsaw Toxic Comments dataset. Produces two sets of production-ready model checkpoints for loading into the [moderation-stream](../moderation-stream/) platform (project 22, Phase 2).

---

## Overview

- Fine-tunes `distilbert-base-uncased` and `roberta-base` as binary toxicity classifiers (`toxic` / `not toxic`)
- Evaluates both fine-tuned models against their zero-shot baselines with per-category breakdown
- Exports checkpoints in `from_pretrained()`-compatible format for direct use in project 22

---

## Dataset

Download the **Jigsaw Toxic Comment Classification Challenge** dataset from Kaggle (free account required):

```
https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge/data
```

Download `train.csv` and place it in a local directory, then configure:

```bash
cp .env.example .env
# Edit .env: set JIGSAW_DATA_DIR=/path/to/directory/containing/train.csv
```

---

## Setup

```bash
export PATH="$HOME/.local/bin:$PATH"
uv sync
```

---

## Training

### DistilBERT

```bash
uv run train --model distilbert --output-dir checkpoints --epochs 4
```

Expected runtime:
- **MPS (Apple Silicon):** ~8–12 min/epoch on full dataset (~144k rows)
- **Colab T4:** ~3–5 min/epoch

For fast local iteration (recommended on MPS for development):

```bash
uv run train --model distilbert --output-dir checkpoints --epochs 2 --max-train-samples 20000
```

Checkpoint saved to: `checkpoints/distilbert-best/`

### RoBERTa

```bash
uv run train --model roberta --output-dir checkpoints --epochs 4
```

Expected runtime:
- **MPS (8GB RAM):** ~15–20 min/epoch — use `--batch-size 8` if memory is tight
- **Colab T4:** ~5–8 min/epoch

**Note:** Default batch size for RoBERTa is 16. Using 32 will OOM on 8GB MPS.

```bash
# 8GB MPS safety
uv run train --model roberta --output-dir checkpoints --epochs 4 --batch-size 8

# Fast local iteration
uv run train --model roberta --output-dir checkpoints --epochs 2 --max-train-samples 20000
```

Checkpoint saved to: `checkpoints/roberta-best/`

---

## Colab Training (T4/A100, ~$1–2 total)

Open `notebooks/colab_training.ipynb` in Google Colab. The notebook installs dependencies, mounts Google Drive, runs both training passes, and saves checkpoints to `My Drive/toxicity-checkpoints/`.

Runtime estimate on T4: ~30–45 minutes total for both models (full dataset, 4 epochs each).

---

## Evaluation

```bash
uv run evaluate --model distilbert --checkpoint-dir checkpoints/distilbert-best

uv run evaluate --model roberta --checkpoint-dir checkpoints/roberta-best
```

Writes a JSON result file to `eval_results/` and prints a summary table showing fine-tuned vs zero-shot F1, precision, recall, AUC-ROC, and per-category accuracy for all six Jigsaw label columns.

---

## Connecting to Project 22 (moderation-stream Phase 2)

Once checkpoints are trained, set these in `projects/moderation-stream/.env`:

```bash
DISTILBERT_CHECKPOINT_PATH=/absolute/path/to/checkpoints/distilbert-best
ROBERTA_CHECKPOINT_PATH=/absolute/path/to/checkpoints/roberta-best
```

The `MODEL_REGISTRY` reads these fields from settings. When set, slots 4 and 5 in the dashboard switch from `pending_weights` to `active` — no code changes required.

---

## Tests

```bash
uv run pytest tests/ -v       # 16 tests, no weight downloads
uv run ruff check .
uv run ruff format --check .
```
