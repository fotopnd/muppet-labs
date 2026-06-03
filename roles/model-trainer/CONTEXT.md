# model-trainer — Role Contract

## Identity

This role validates prerequisites, executes a fine-tuning pipeline, evaluates the resulting checkpoint, and produces a structured handoff for downstream consumers. It drives CLI entry points in target projects (`uv run train`, `uv run evaluate`) — it does not implement training code. Invoke it for any new fine-tuning run on an established training project that exposes `train` and `evaluate` entry points via uv.

---

## Inputs

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `project_dir` | Path | — | Yes | Absolute path to the target project root |
| `dataset_path` | Path | — | Yes | Absolute path to training data file |
| `dataset_env_var` | str | — | Yes | Name of the env var in `.env` that holds the dataset path (e.g. `JIGSAW_DATA_DIR`, `IMDB_DATA_DIR`) |
| `smoke_run` | bool | `true` | No | Set `false` to skip smoke run on reruns |
| `models` | list | — | Yes | One entry per model to train; processed in order (see sub-fields below) |
| `models[].key` | str | — | Yes | Model identifier passed to `--model` flag |
| `models[].epochs` | int | `4` | No | Number of training epochs for the full run |
| `models[].batch_size` | int | see constraints | No | Batch size for full run; defaults per Device/Architecture Constraints |
| `models[].baseline_checkpoint` | str | `null` | No | HuggingFace model ID for evaluation comparison; omit if no baseline applies |

---

## Device / Architecture Constraints

Read before issuing any training commands.

- **`bf16: false`** — never pass on MPS. Support is inconsistent and causes silent gradient corruption.
- **`pin_memory`** — do not pass. MPS does not support pinned memory; the CLI should not include this flag.
- **Large-encoder-class models** (RoBERTa, BERT-large, etc.): default `batch_size: 8` on Apple Silicon 8 GB unified memory. Higher values cause OOM.
- **Small-encoder-class models** (DistilBERT, ALBERT-base, etc.): default `batch_size: 32` on Apple Silicon 8 GB.
- **Checkpoint path:** `resources/models/<project-name>/<model-key>-<YYYY-MM-DD>/` — workspace-level, shared across consuming projects. `<project-name>` is the training project's directory name (e.g. `toxicity-classifier-finetuned`).
- **Eval results path:** `resources/evals/<project-name>/<model-key>-<timestamp>.json` — written by `uv run evaluate`. The model-trainer role reads this file in step 2.4.
- **Smoke dir:** `<project_dir>/checkpoints/.smoke-<model-key>/` — project-local temp directory, cleaned up after human confirms the smoke run.
- **Same-day reruns:** append `-v2`, `-v3` to the checkpoint directory rather than overwriting.

---

## Process

1. **Validate prerequisites**
   - 1.1. Confirm `dataset_path` exists: `ls -lh <dataset_path>`
   - 1.2. Confirm `<project_dir>/.env` is present
   - 1.3. Run `grep "^<dataset_env_var>=" <project_dir>/.env` and confirm the extracted value matches `dataset_path`. Hard stop if the var is absent or the path differs.
   - 1.4. Run `cd <project_dir> && uv sync`
   - → **Hard stop** if any check fails. Report the specific failing check with the actual vs expected value. Do not proceed.

2. **For each model in `models:` — repeat steps 2.1–2.5 in declared order**
   - 2.1. *(skip if `smoke_run: false`)* **Smoke run:**
     ```
     uv run train --model <key> --output-dir <smoke_dir> --epochs 2 --max-train-samples 20000
     ```
     Print: epoch 2 val_loss, epoch 2 val_F1, estimated full-run wall time at this throughput.
     → **Wait for human sign-off.** On approval, clean up smoke dir: `rm -rf <smoke_dir>`
   - 2.2. **Full training run:**
     ```
     uv run train --model <key> --output-dir <checkpoint_dir> --epochs <epochs> --batch-size <batch_size>
     ```
   - 2.3. **Evaluate:**
     ```
     uv run evaluate --model <key> --checkpoint-dir <checkpoint_dir>
     ```
     Append `--baseline-checkpoint <baseline_checkpoint>` if provided.
   - 2.4. **Read epoch log** from `<checkpoint_dir>/epoch_log.json` and eval results from `resources/evals/<project-name>/<model-key>-<timestamp>.json` — extract per-epoch train loss, val loss, val F1, and final metrics.
   - 2.5. **Write output section** for this model to `output/output.md` (fill all sections per Output template).

3. **Write Session Summary** table to `output/output.md`.

---

## Output

**File:** `roles/model-trainer/output/output.md`

**Required sections — one block per model, then Session Summary:**

```
## Model: <key>

### Checkpoint
- **Path:** <absolute path>
- **Verify:** `ls -lh <path>/config.json`

### Eval Metrics
| Metric     | Fine-tuned | Baseline (if provided) |
|------------|-----------|------------------------|
| F1         |           |                        |
| Precision  |           |                        |
| Recall     |           |                        |
| AUC-ROC    |           |                        |

### Per-Class Breakdown (if project CLI produces it)
[paste evaluate CLI stdout verbatim — format is project-specific]

### Epoch Log
| Epoch | Train Loss | Val Loss | Val F1 |
|-------|-----------|---------|--------|

### Downstream Wiring
| Env Var | Value | File to Edit |
|---------|-------|-------------|

---

## Session Summary
| Model | Checkpoint | Best Val F1 | Status |
|-------|-----------|------------|--------|
```

---

## Notes

- `epoch_log.json` must be present at `<checkpoint_dir>/epoch_log.json` for step 2.4 to succeed. If the target project writes the log to a different path, note the actual path in the Inputs for that invocation.
- `smoke_run: false` skips step 2.1 entirely — estimated wall time is not shown. The human accepts this means no fast-fail validation before the full run.
- The role does not download datasets and does not run tests — both are the human's responsibility before invoking the role.
- This role does not modify any project source files. It reads `.env` for validation only.
- Checkpoint paths written to `output/output.md` must use the workspace-level path (`resources/models/...`), not the project-local path. Consuming projects (e.g. moderation-stream) reference these paths via env vars — the workspace-level path is stable regardless of where the training project lives.
- If `uv run train` or `uv run evaluate` fails, write the model's output section with whatever data is available, set the Session Summary status to `failed`, and stop. Do not proceed to the next model.
- If the target dataset has fewer than 20,000 samples, `--max-train-samples 20000` in the smoke run is silently ignored and the full dataset is used. Wall time estimates from the smoke run will be accurate rather than conservative — this is acceptable.
