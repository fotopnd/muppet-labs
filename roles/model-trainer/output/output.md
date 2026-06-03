# model-trainer Output

**Role:** model-trainer
**Project:** toxicity-classifier-finetuned
**Date:** 2026-06-03

---

## Model: distilbert

### Checkpoint
- **Path:** `/Users/fotopnd/Documents/muppet-labs/resources/models/toxicity-classifier-finetuned/distilbert-best`
- **Verify:** `ls -lh /Users/fotopnd/Documents/muppet-labs/resources/models/toxicity-classifier-finetuned/distilbert-best/config.json`

### Eval Metrics
| Metric     | Fine-tuned | Zero-shot baseline |
|------------|-----------|-------------------|
| F1         | 0.8473    | 0.3223            |
| Precision  | 0.8282    | 0.2056            |
| Recall     | 0.8672    | 0.7449            |
| AUC-ROC    | 0.9241    | 0.7200            |

### Per-Class Breakdown
```
Per-category accuracy (fine-tuned prediction vs label):
  severe_toxic         ft=0.9090  zs=0.6600  Δ=+0.2490
  obscene              ft=0.9487  zs=0.6855  Δ=+0.2633
  threat               ft=0.9023  zs=0.6552  Δ=+0.2471
  insult               ft=0.9460  zs=0.6844  Δ=+0.2616
  identity_hate        ft=0.9083  zs=0.6579  Δ=+0.2503
```

### Epoch Log
| Epoch | Train Loss | Val Loss | Val F1 |
|-------|-----------|---------|--------|
| 1     | —         | 0.0804  | 0.8276 |
| 2     | —         | 0.0821  | **0.8349** ← best |
| 3     | —         | 0.0922  | 0.8211 |
| 4     | —         | 0.1060  | 0.8270 |

> Train loss not captured in epoch log (HuggingFace Trainer logs it separately at `logging_steps=50`). Val loss rising after epoch 2 indicates mild overfitting; `load_best_model_at_end=True` saved epoch 2 checkpoint.

### Downstream Wiring
| Env Var | Value | File to Edit |
|---------|-------|-------------|
| `DISTILBERT_CHECKPOINT_PATH` | `/Users/fotopnd/Documents/muppet-labs/resources/models/toxicity-classifier-finetuned/distilbert-best` | `projects/moderation-stream/.env` |

---

## Model: roberta

> **Status: PENDING** — overnight run scheduled. batch_size=32, ~6h on Apple M4 MPS.
> Command: `caffeinate -i uv run train --model roberta --output-dir checkpoints --epochs 4 --batch-size 32`
> This section will be filled after the run completes.

---

## Session Summary
| Model      | Checkpoint                                                          | Best Val F1 | Status  |
|------------|---------------------------------------------------------------------|-------------|---------|
| distilbert | `resources/models/toxicity-classifier-finetuned/distilbert-best`   | 0.8349      | ✓ done  |
| roberta    | `resources/models/toxicity-classifier-finetuned/roberta-best`      | —           | pending |
