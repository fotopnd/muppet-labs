# Planner Output — toxicity-classifier-finetuned

**Role:** planner
**Sequence:** `new-project-full` (step 2)
**Date:** 2026-06-03

---

## Project

`toxicity-classifier-finetuned` — a PyTorch fine-tuning pipeline that trains DistilBERT and RoBERTa on the Jigsaw Toxic Comments dataset and exports production-ready checkpoints for moderation-stream (project 22) Phase 2.

---

## Brief Flags Resolved

**Flag 1 — Binary vs multi-label training objective.**
Confirmed: binary. The `toxic` column is the training target. Binary classification produces a well-calibrated toxic/not-toxic decision, which is what project 22 needs to compute accuracy vs ground-truth labels at inference time. Multi-label would require BCEWithLogitsLoss per label, a separate output head per label, and threshold tuning per category — added complexity with no benefit to the project 22 use case. The six fine-grained labels are evaluation-only: per-category accuracy is computed after inference by checking each label column against the binary prediction.

**Flag 2 — `roberta-base` vs `roberta-large`.**
Confirmed: `roberta-base`. Project 22 requires CPU inference at 5–50ms per classification. `roberta-large` (355M parameters) will exceed this on most CPU hardware. `roberta-base` (125M parameters) is in the same weight class as DistilBERT (66M) and will meet the latency target.

**Flag 3 — Colab fallback.**
Decision: Colab notebook is a deliverable. MPS fine-tuning runs at ~4–8 min/epoch for DistilBERT and ~10–15 min/epoch for RoBERTa on typical splits (10k+ rows). With 3–5 epochs each that is 30–100 minutes of wall time — feasible but slow. A Colab T4 notebook is included as an explicit deliverable: it runs the same training code, saves checkpoints to Google Drive, and documents the T4 runtime cost (~$1–2 total).

---

## Requirements

1. The data pipeline loads the Jigsaw Toxic Comments CSV from a path configured by `JIGSAW_DATA_DIR` env var and returns train/val/test splits (80/10/10) with a fixed seed (42) for reproducibility.
2. The tokeniser wraps `AutoTokenizer` for the given model checkpoint and truncates to max 128 tokens — sufficient for short comment text.
3. The DistilBERT training script fine-tunes `distilbert-base-uncased` as `AutoModelForSequenceClassification(num_labels=2)` on the binary `toxic` label, saves the best checkpoint by validation F1, and emits training/validation loss and F1 per epoch to a JSON log file.
4. The RoBERTa training script fine-tunes `roberta-base` as `AutoModelForSequenceClassification(num_labels=2)` with the same objective and logging format as DistilBERT.
5. Both training scripts accept `--output-dir`, `--epochs`, `--batch-size`, `--lr`, and `--max-train-samples` CLI flags with documented defaults; all other hyperparameters are fixed in code.
6. Both training scripts detect and use MPS if available, fall back to CUDA if available, fall back to CPU via a shared `get_device()` utility.
7. The evaluation script loads a saved checkpoint, runs inference on the held-out test set, and produces: overall F1, precision, recall, AUC-ROC; per-category accuracy for each of the six Jigsaw labels; and a comparison row for the zero-shot baseline (the same zero-shot pipeline checkpoint used by project 22 Phase 1).
8. The evaluation script writes results to `eval_results/<model-slug>-<timestamp>.json` and prints a formatted summary table to stdout.
9. Checkpoints are saved via `model.save_pretrained(output_dir)` and `tokenizer.save_pretrained(output_dir)` — format is directly loadable by project 22 via `from_pretrained(path)`.
10. A `train` CLI entry point runs either `distilbert` or `roberta` training via `--model {distilbert,roberta}` flag.
11. An `evaluate` CLI entry point runs evaluation for a given `--checkpoint-dir` and `--model {distilbert,roberta}`.
12. All tests pass via `uv run pytest` with no live model downloads required (model weights are mocked using random weight tensors sized to match the real architecture).
13. `ruff check` and `ruff format --check` pass on the entire project.
14. `README.md` documents: dataset download steps, training commands, evaluation commands, expected runtime on MPS and Colab T4, and how to configure checkpoint paths in project 22.

---

## Technology Stack

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | Workspace standard; `StrEnum`, `X \| Y` union syntax |
| Package manager | uv | Workspace standard |
| Formatter / linter | ruff | Workspace standard |
| ML framework | PyTorch ≥2.2 | Direct MPS support; HuggingFace integrates natively |
| Model loading | `transformers` ≥4.40 | `AutoModelForSequenceClassification`, `AutoTokenizer`, `Trainer` |
| Dataset loading | `datasets` (HuggingFace) | Tokenised dataset caching; arrow format reduces repeat tokenisation cost |
| Metrics | `scikit-learn` | F1, precision, recall, AUC-ROC; well-tested |
| CLI | `typer` | Consistent with other muppet-labs projects; typed args |
| Testing | `pytest` | Workspace standard |
| Notebook (optional) | Colab-compatible `.ipynb` | Local dev optional; Colab T4 is the fast-path runtime |

---

## File and Module Structure

```
projects/toxicity-classifier-finetuned/
├── pyproject.toml                     # uv project; hatchling; train + evaluate CLI entry points
├── ruff.toml                          # line-length=100, E/F/I/UP/B
├── .env.example                       # JIGSAW_DATA_DIR, MODEL_OUTPUT_DIR
├── .gitignore
├── README.md                          # setup, training, eval, Colab, project 22 integration
│
├── toxicity_classifier/
│   ├── __init__.py
│   ├── config.py                      # pydantic-settings Settings; JIGSAW_DATA_DIR, MODEL_OUTPUT_DIR
│   ├── device.py                      # get_device() → torch.device (MPS → CUDA → CPU)
│   ├── data.py                        # load_jigsaw(), tokenise_dataset(), get_splits()
│   ├── train_distilbert.py            # train() for distilbert-base-uncased
│   ├── train_roberta.py               # train() for roberta-base
│   ├── evaluate.py                    # evaluate() loads checkpoint, runs test set, writes JSON
│   └── cli.py                         # train and evaluate CLI commands (typer)
│
├── notebooks/
│   └── colab_training.ipynb           # Colab T4 notebook; same training code; Drive checkpoint save
│
├── eval_results/                      # .gitignore'd; evaluation JSON outputs land here
│   └── .gitkeep
│
└── tests/
    ├── __init__.py
    ├── conftest.py                     # fixtures: tmp_dir, mock_csv, mock_model_factory
    ├── test_data.py                    # CSV loading, split ratios, tokenisation output shape
    ├── test_train.py                   # single forward pass + loss step with mocked weights
    └── test_evaluate.py               # checkpoint round-trip, metric shape, JSON output schema
```

---

## Open Questions for Architect

1. **Training loop implementation:** HuggingFace `Trainer` vs manual PyTorch loop. Proposed answer: `Trainer`-based with inline comments explaining each key `TrainingArguments` field — the portfolio signal comes from the evaluation module and clean architecture, not from re-implementing gradient accumulation. No separate `train_manual.py`.

2. **MPS + bf16 compatibility:** PyTorch MPS supports `bfloat16` from 2.4+. Proposed answer: default fp32 on MPS; bf16 enabled only when device is CUDA. `get_device()` returns the device and a `use_bf16: bool` flag; `TrainingArguments` uses that flag. Document this in both training modules.

3. **`--max-train-samples` flag:** Proposed answer: expose on both training CLIs with default `None` (full set). The Colab notebook uses full set; local MPS development uses 20k for fast iteration. Document recommended values in README.

4. **Evaluation zero-shot baseline:** Proposed answer: use the same zero-shot pipeline checkpoint that project 22's Phase 1 uses (`distilbert-base-uncased-finetuned-sst-2-english` for DistilBERT slot, `roberta-large-mnli` for RoBERTa slot) so the evaluation comparison directly reflects the improvement the fine-tuned weights deliver on the live platform. The architect should confirm these checkpoint names against project 22's consumer config.

---

## Handoff

**Next role:** architect
**What the architect does with this:**
- Accept or override the four proposed answers to open questions above.
- Define internal function signatures and data flow for each module (`data.py`, `train_distilbert.py`, `train_roberta.py`, `evaluate.py`, `cli.py`).
- Define the `Trainer` configuration: which `TrainingArguments` fields are set and why.
- Define `compute_metrics` return structure and how it feeds the JSON log.
- Define the evaluation output JSON schema.
- Confirm `pyproject.toml` `[project.scripts]` entry names (`train`, `evaluate`).
- Confirm zero-shot baseline checkpoint names against project 22 config (cross-check `projects/moderation-stream/moderation_stream/config.py`).

**Flags for architect:**
- Open question 4 (zero-shot baseline checkpoints) requires cross-referencing project 22's `MODEL_REGISTRY` — do this before designing `evaluate.py` to ensure the comparison is apples-to-apples.
- Open question 3 (`--max-train-samples`) affects CLI signature; lock in before implementer writes argument parsing.
