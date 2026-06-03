# Architect Output — model-trainer

**Role:** architect
**Sequence:** `new-project-full` (step 3)
**Date:** 2026-06-03

---

## System Overview

The model-trainer is a workspace process role, not a software system. Its deliverables are two files: `roles/model-trainer/CONTEXT.md` (the role contract the agent executes) and `roles/model-trainer/output/output.md` (a blank template that shows the role's runtime output structure). The role drives CLI entry points in target projects under `projects/` — it does not own any training code. Its moving parts are the role contract itself, the structured input schema that parameterises each invocation, and the output template that the role fills in at runtime.

The role is generic: it makes no assumptions about dataset format, label schema, or model architecture beyond what the target project's CLI exposes. Project-specific details (dataset env var name, label categories, baseline model IDs) are all supplied at invocation time via the Inputs section.

---

## Open Questions Resolved

**OQ1 — Human gate placement:**
Confirmed: one gate per model, placed after smoke run and before full run. When `models: [distilbert, roberta]`, the gate fires twice — once per model. The sequence for two models is: model-A smoke → gate → model-A full → model-A eval → model-B smoke → gate → model-B full → model-B eval. The output has a top-level section per model.

**OQ2 — Checkpoint path convention:**
`output_dir` is a derived value, not an input field. The role computes it as `<project_dir>/checkpoints/<model-key>-<YYYY-MM-DD>/`. Smoke run uses a parallel temp path `<project_dir>/checkpoints/.smoke-<model-key>/` that is cleaned up after the human confirms. The derivation formula is documented in the CONTEXT.md Device/Architecture Constraints section.

**OQ3 — `max_train_samples` in full run:**
Confirmed: full run never uses `max_train_samples`. The `smoke_run: false` flag skips the smoke run entirely; it does not affect full run parameters.

**OQ4 — Baseline comparison source:**
`baseline_checkpoint` is an optional field per model entry. Not all projects have a meaningful baseline — omitting it produces an output with only fine-tuned metrics. When provided, the evaluate CLI receives it and the output includes a comparison column. The role contract does not assume a zero-shot baseline exists.

---

## Data Models

### Input Schema (Inputs section of CONTEXT.md)

```
project_dir: Path          # absolute path to target project root
dataset_env_var: str        # name of the env var in .env that holds the dataset path
                            # (e.g. JIGSAW_DATA_DIR, IMDB_DATA_DIR — project-specific)
dataset_path: Path          # absolute path to training data (validated against dataset_env_var)
smoke_run: bool             # default: true; set false to skip smoke run on reruns
models:                     # one entry per model to train; processed in order
  - key: str                # model identifier passed to --model flag
    epochs: int             # number of training epochs for full run (default: 4)
    batch_size: int         # batch size for full run; see Device/Architecture Constraints
    baseline_checkpoint: str | null  # optional; HuggingFace model ID for comparison baseline
```

`dataset_env_var` decouples the role from project-specific env var naming. The role validates that the var is present in `.env` and that its value matches `dataset_path`.

### Output File Schema (per model, in output/output.md)

```markdown
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
[paste evaluate CLI stdout here — format is project-specific]

### Epoch Log
| Epoch | Train Loss | Val Loss | Val F1 |
|-------|-----------|---------|--------|

### Downstream Wiring
| Env Var | Value | File to Edit |
|---------|-------|-------------|
```

The Per-Class Breakdown section is free-form: paste the evaluate CLI output verbatim. Its format is owned by the target project, not this role. The role does not attempt to parse or reformat it.

---

## Module Interfaces

### `CONTEXT.md` — Required Sections and Their Contracts

The implementer writes this file. Each section has a defined purpose and content rule.

**Section 1: Identity**
One paragraph. States: what the role is, what it drives (not owns), and when to invoke it (any new fine-tuning run on an established training project that exposes `train` and `evaluate` CLI entry points via uv).

**Section 2: Inputs**
Table with five columns: Field, Type, Default, Required, Description. Matches the Input Schema above exactly.

**Section 3: Device / Architecture Constraints**
Bullet list. Must include:
- `bf16: false` — required on MPS; inconsistent support causes silent gradient corruption
- `pin_memory` — do not pass; MPS does not support pinned memory
- Large-encoder-class models (RoBERTa, BERT-large, etc.): default `batch_size: 8` on Apple Silicon 8 GB
- Small-encoder-class models (DistilBERT, ALBERT-base, etc.): default `batch_size: 32` on Apple Silicon 8 GB
- Checkpoint path derivation: `<project_dir>/checkpoints/<model-key>-<YYYY-MM-DD>/`
- Smoke dir: `<project_dir>/checkpoints/.smoke-<model-key>/` — cleaned up post-confirmation

**Section 4: Process**
Numbered steps. The per-model loop is a sub-list under step 2 (numbered 2.1 through 2.5):

```
1. Validate prerequisites
   1.1. Confirm dataset_path exists: `ls -lh <dataset_path>`
   1.2. Confirm <project_dir>/.env is present
   1.3. Confirm <dataset_env_var> in .env resolves to dataset_path
   1.4. Run `cd <project_dir> && uv sync`
   → Hard stop if any check fails. Report the specific failing check and do not proceed.

2. For each model in models: (repeat 2.1–2.5 per model in declared order)
   2.1. [skip if smoke_run: false] Smoke run:
        `uv run train --model <key> --output-dir <smoke_dir> --epochs 2 --max-train-samples 20000`
        Print: epoch 2 val_loss, epoch 2 val_F1, estimated full-run wall time at this throughput.
        → Wait for human sign-off. On approval, clean up smoke_dir: `rm -rf <smoke_dir>`
   2.2. Full training run:
        `uv run train --model <key> --output-dir <checkpoint_dir> --epochs <epochs> --batch-size <batch_size>`
   2.3. Evaluate:
        `uv run evaluate --model <key> --checkpoint-dir <checkpoint_dir>` 
        [append `--baseline-checkpoint <baseline_checkpoint>` if provided]
   2.4. Read epoch log from <checkpoint_dir>/epoch_log.json — extract per-epoch train loss, val loss, val F1.
   2.5. Write output section for this model to output/output.md.

3. Write Session Summary section to output/output.md.
```

**Section 5: Output**
States: file path (`roles/model-trainer/output/output.md`), required top-level sections, schema for each section. Notes that the output accumulates one section per model plus a final Session Summary.

**Section 6: Notes**
- Same-day reruns: append `-v2`, `-v3` to the checkpoint directory name rather than overwriting.
- `smoke_run: false` skips step 2.1 entirely; estimated wall time is not shown.
- `epoch_log.json` must be present at `<checkpoint_dir>/epoch_log.json` for step 2.4 to succeed. If the target project's CLI writes the log to a different path, document the actual path in the Inputs section for that invocation.
- The role does not download datasets and does not run tests — both are the human's responsibility before invoking the role.

---

## Dependencies

```
roles/model-trainer/CONTEXT.md
    reads from: project_dir/.env, dataset_path (validated, not modified)
    drives: project_dir CLI (uv run train, uv run evaluate)
    writes to: roles/model-trainer/output/output.md

roles/model-trainer/output/output.md
    read by: human for sign-off and downstream wiring
    read by: any consuming project (for env var values to set)
```

No circular dependencies. The role is a pure driver — it reads inputs, invokes CLIs, and writes a report.

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Error handling | Hard stop on any prerequisite failure; print the specific check that failed. No silent fallbacks. |
| Configuration | All configuration lives in the Inputs section. The role validates existing `.env` — it does not create or modify one. |
| Logging | Training logs written by the project CLI to `<checkpoint_dir>/epoch_log.json`. The role reads this in step 2.4. |
| Testing | Role contract is Markdown; no automated tests. Smoke run is the functional validation gate. |
| Checkpoint naming | Date-stamped directories prevent reruns from overwriting. Version suffix handles same-day reruns. |

---

## Implementation Notes for Implementer

- The implementer's only deliverable is `roles/model-trainer/CONTEXT.md`. No source code is written.
- Also create `roles/model-trainer/output/output.md` as a blank template — all required sections present with placeholder content, showing what a completed run looks like.
- Device/Architecture Constraints must appear between Inputs and Process. It is read before any commands are issued.
- Process step numbering: use 1 / 2.1 / 2.2 / ... format. The sub-list makes the per-model loop visually distinct.
- The Session Summary section in output.md is a table: model key, checkpoint path, best val_F1, status (complete / failed). One row per model.
- The Per-Class Breakdown section in the output template is free-form (labelled "paste evaluate CLI stdout here"). Do not attempt to structure it in the template — it varies per project.
- Keep the CONTEXT.md to six sections, one screen. Do not add prose beyond what is specified.

---

## Handoff

**Next role:** implementer

The implementer reads this file and writes `roles/model-trainer/CONTEXT.md` exactly as specified. All four open questions are resolved. No design decisions remain for the implementer to make.

**Flags for implementer:**
- The Device/Architecture Constraints section position (between Inputs and Process) is required.
- The blank `output/output.md` template is a second deliverable — do not omit it.
- `dataset_env_var` is a new field not in the brief — it is the key generalisation that makes the role project-agnostic. Make sure its description in the Inputs table is clear.
