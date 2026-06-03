# Implementer Output — toxicity-classifier-finetuned

**Role:** implementer
**Sequence:** `new-project-full` (step 6)
**Date:** 2026-06-03

---

## Files Produced

| File | Purpose |
|------|---------|
| `pyproject.toml` | uv project; hatchling build; `train` and `evaluate` CLI entry points; pytest config |
| `ruff.toml` | line-length=100; E/F/I/UP/B; notebooks/ excluded |
| `.env.example` | JIGSAW_DATA_DIR, MODEL_OUTPUT_DIR |
| `.gitignore` | Standard Python + checkpoints/ + eval_results/*.json + data/ |
| `README.md` | Dataset download, training commands, expected runtimes, Colab usage, project 22 integration |
| `toxicity_classifier/__init__.py` | Package marker |
| `toxicity_classifier/config.py` | pydantic-settings Settings; JIGSAW_DATA_DIR, MODEL_OUTPUT_DIR |
| `toxicity_classifier/device.py` | `get_device()` → `DeviceConfig(device, use_bf16)`; MPS → CUDA → CPU |
| `toxicity_classifier/metrics.py` | `make_compute_metrics()` for HuggingFace Trainer; binary F1 |
| `toxicity_classifier/data.py` | `load_jigsaw()`, `get_splits()`, `tokenise_splits()`; category columns preserved in test split |
| `toxicity_classifier/train_distilbert.py` | `train()` for `distilbert-base-uncased`; saves `distilbert-best/` checkpoint |
| `toxicity_classifier/train_roberta.py` | `train()` for `roberta-base`; saves `roberta-best/` checkpoint; default batch=16 |
| `toxicity_classifier/evaluate.py` | `evaluate()` loads checkpoint, runs fine-tuned + zero-shot inference, writes JSON + prints table |
| `toxicity_classifier/cli.py` | `run_train()` and `run_evaluate()` entry point wrappers; two Typer apps |
| `notebooks/colab_training.ipynb` | Colab T4 notebook; Drive mount; trains both models; downloads zip |
| `eval_results/.gitkeep` | Preserves empty results directory in git |
| `tests/__init__.py` | Package marker |
| `tests/conftest.py` | Fixtures: `tmp_data_dir`, `mock_distilbert_model`, `mock_roberta_model`, `mock_tokenizer` |
| `tests/test_data.py` | 7 tests: CSV loading, missing file, missing columns, split sizes, max_train_samples, tokenisation shape, category column retention |
| `tests/test_train.py` | 4 tests: forward pass + loss (both models), checkpoint creation (both models, patched weights) |
| `tests/test_evaluate.py` | 5 tests: perfect metrics, all-wrong metrics, binary predictions, JSON output, EvalResult structure |

---

## Setup Steps Taken

```bash
uv init toxicity-classifier-finetuned --python 3.12
uv add torch transformers datasets scikit-learn typer pydantic-settings pandas accelerate
uv add --dev pytest ruff
```

`accelerate` was added after setup — required by HuggingFace `Trainer` in transformers 5.x (not documented at planner stage; added when test revealed `ImportError`).

---

## Deviations from Architecture

1. **`accelerate` dependency added.** `transformers.Trainer` in version 5.9.0 requires `accelerate>=1.1.0` at `TrainingArguments` init time. Not known at planning/architect stage. Added to `pyproject.toml`.

2. **`no_cuda` removed from `TrainingArguments`.** The `no_cuda` argument was removed in transformers 5.x. Replaced with no explicit device flag — the Trainer auto-detects MPS/CUDA/CPU, which is the correct behaviour for this project. `DeviceConfig` still controls `bf16`.

3. **`warmup_ratio` replaced with `warmup_steps=100`.** `warmup_ratio` is deprecated in transformers 5.2+. Fixed to 100 steps, which is approximately 10% of a typical 1k-step epoch on the default 80% training split.

4. **Patch target in train tests is `transformers.*`, not `toxicity_classifier.train_*.AutoModelForSequenceClassification`.** Since `transformers` imports are deferred inside `train()` function bodies, there is no module-level name to patch. Tests patch at the source (`transformers.AutoModelForSequenceClassification.from_pretrained`).

5. **`metrics.py` extracted as shared module.** `make_compute_metrics()` is identical for both training modules. Extracted to avoid duplication — minor divergence from architect spec which showed it inline.

6. **`_make_tiny_training_args` helper removed from `test_train.py`.** Unused after tests were rewritten to use the actual `train()` function rather than a manual `Trainer` setup.

---

## Known Gaps

- **`pyproject.toml` asyncio_mode setting is unused.** Left over from workspace template. Not harmful; no async tests exist. Remove at reviewer's discretion.
- **Colab notebook can't be linted** — excluded from ruff (`notebooks/` in exclude list) due to Colab-specific import ordering patterns. Notebook is correct as written.
- **Zero-shot baseline downloads model weights on first `evaluate` run.** `typeform/distilbert-base-uncased-mnli` (~260MB) and `roberta-large-mnli` (~1.4GB) download to HuggingFace cache. This is expected but not explicitly documented in the README. Reviewer may want to add a note.
- **`_get_raw_test` in `evaluate.py` reproduces the split rather than caching it.** Correct (same seed=42, same stratify logic), but slightly redundant. Acceptable for a portfolio build.

---

## How to Run

```bash
# Verify setup (no model downloads)
uv run pytest tests/ -v   # 16 tests, all pass

# Lint check
uv run ruff check .
uv run ruff format --check .

# CLI smoke test (requires .env with JIGSAW_DATA_DIR set)
uv run train --help
uv run evaluate --help

# Fast training run (MPS, development)
uv run train --model distilbert --epochs 1 --max-train-samples 1000 --output-dir /tmp/test-checkpoints
```

---

## Handoff

**Next role:** reviewer
**What the reviewer checks:**
- Correctness of `tokenise_splits()`: category columns must survive into the test split (covered by `test_tokenise_splits_test_retains_category_columns`).
- Correctness of `_get_raw_test()` in `evaluate.py`: must use identical seed and stratify parameters as `get_splits()` — any divergence produces a test set data leak.
- Test coverage: confirm no untested non-trivial branches remain.
- `asyncio_mode` in pyproject.toml — flag for removal.
- Deviation 4 (patch target) — confirm this is the correct approach for deferred imports in HuggingFace projects.

**Flags for reviewer:**
- Deviation 2 (`no_cuda` removal): the training loop now runs on MPS by default on Mac, which is correct. But the test runs may also use MPS if available. The tests use tiny random models so this is fast, but the reviewer should confirm the test output shows no unexpected device usage.
- Known gap (zero-shot baseline weight downloads): whether to document this in README is a judgment call for the reviewer.
