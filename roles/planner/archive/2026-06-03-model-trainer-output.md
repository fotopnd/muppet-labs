# Planner Output — model-trainer

**Role:** planner
**Sequence:** `new-project-full` (step 2)
**Date:** 2026-06-03

---

## Project

`model-trainer` — a reusable workspace role that validates prerequisites, executes a fine-tuning pipeline (smoke run + full run), evaluates the resulting checkpoint, and produces a structured handoff for downstream consumers. It drives existing training CLI entry points; it does not implement them.

---

## Brief Flags Resolved

**Flag: one model at a time vs. multi-model**
Decision: the role accepts a `models:` list in its Inputs section. The Process steps iterate over the list in sequence. The output has a section per model. Invoking with `models: [distilbert, roberta]` runs them back-to-back with a human confirmation gate between the smoke run and the full run for each. This eliminates the need for two separate role invocations while preserving human oversight at the most expensive decision point. The architect should confirm whether the confirmation gate is a single "proceed?" at the start of each model's full run or after each model completes.

---

## Requirements

1. The role contract (`roles/model-trainer/CONTEXT.md`) specifies all required inputs: `project_dir` (absolute path), `models` (list of model keys), `dataset_path` (absolute path), `epochs`, `batch_size`, and an optional `max_train_samples` field for smoke-and-fast-run mode.
2. The role's first process step validates all prerequisites before any training command runs: (a) `dataset_path` file exists, (b) `.env` is present and contains a valid value for the dataset env var, (c) `uv sync` completes cleanly. If any check fails, the role stops and reports the specific failure.
3. Smoke run is required on the first invocation for any new model/dataset combination. Smoke run uses `--epochs 2 --max-train-samples 20000`. Smoke run is skippable via an explicit `smoke_run: false` input flag on reruns.
4. After the smoke run, the role pauses for human sign-off (shows: epoch 2 val_loss, val_F1, estimated full-run wall time) before the full training run begins.
5. Full training run uses the `epochs` and `batch_size` values from the Inputs section. MPS device constraints are hardcoded into the role contract: `--batch-size 8` default for RoBERTa-class models on Apple Silicon; `bf16` never passed.
6. After full training completes, the evaluation step runs automatically: `uv run evaluate --model <key> --checkpoint-dir <output_dir>`.
7. The role output file (`output/output.md`) must contain, for each model: absolute checkpoint path, eval metrics table (F1, precision, recall, AUC-ROC — fine-tuned vs zero-shot baseline), epoch loss curve summary (loss and F1 per epoch from the JSON log), and downstream wiring instructions.
8. Downstream wiring instructions are structured as a table: env var name, value (absolute path), file to edit. Generic enough to cover any consumer project.
9. The role contract is generic: model keys are input variables. The contract does not hardcode `distilbert` or `roberta` — it references `<model-key>` as a placeholder and notes MPS batch-size constraints as a device/architecture matrix in the contract.
10. Checkpoint paths in the output are absolute and include a one-line shell command to confirm the files exist (`ls -lh <checkpoint_dir>/pytorch_model.bin` or `config.json`).
11. The role contract includes a Device/Architecture Constraints section documenting known MPS compatibility rules: no `bf16`, no `pin_memory` flag, RoBERTa-class batch-size cap at 8 for 8 GB unified memory.

---

## Technology Stack

This is a workspace process role — it drives Python/PyTorch/HuggingFace projects rather than implementing them. The deliverables are Markdown files.

| Concern | Choice | Reason |
|---------|--------|--------|
| Role contract format | Markdown (`CONTEXT.md`) | Standard role contract format per workspace spec |
| Role output format | Markdown (`output.md`) | Standard role output format per workspace spec |
| Training CLI | `uv run train --model <key>` | Established pattern from project 8; generic across model keys |
| Evaluation CLI | `uv run evaluate --checkpoint-dir <dir> --model <key>` | Established pattern from project 8 |
| Device detection | Deferred to `device.py` in target project | Role invokes the CLI; device detection is the project's responsibility |
| Checkpoint format | `save_pretrained()` / `from_pretrained()` | HuggingFace standard; directly loadable by consumer projects |

---

## File and Module Structure

```
roles/model-trainer/
├── CONTEXT.md              ← role contract: Inputs, Process, Output, Device Constraints
└── output/
    └── output.md           ← written at runtime; one section per model key in models: list
```

No `archive/` subdirectory pre-created — it is created on first archival per routing.md convention.

The role produces no source code. It drives CLI commands in target projects under `projects/`.

---

## Open Questions for Architect

1. **Human confirmation gate placement.** The brief and requirements specify a gate after smoke run and before full run. Should there also be a gate between models when `models: [distilbert, roberta]`? Proposed answer: yes, one gate per model (after smoke, before full) — this lets the human abort the second model if the first produced unexpected results. Architect should confirm this matches the output structure (if yes, the output has a per-model subsection with its own status field).

2. **Checkpoint path convention.** Where within the project directory should the role write checkpoints? Proposed answer: `<project_dir>/checkpoints/<model-key>-<YYYY-MM-DD>/` — date-stamped so reruns don't overwrite. The role contract specifies this and the CLI `--output-dir` value is derived from it. Architect confirms whether this is a role-computed default or a required input field.

3. **`max_train_samples` in full run.** Should the full run ever use `max_train_samples`? Proposed answer: no — full run always uses the entire dataset. `max_train_samples` is only for smoke run. The `smoke_run: false` flag skips the smoke run but does not limit the full run. Architect should confirm this is unambiguous in the contract language.

4. **Zero-shot baseline source in evaluation.** The evaluation step compares fine-tuned results against a zero-shot baseline. The role contract must specify where the baseline comes from. Proposed answer: the Inputs section includes an optional `zero_shot_checkpoint` field per model key. If omitted, the evaluate CLI uses its project-level default. The role contract documents that the baseline should match the Phase 1 consumer checkpoint in the downstream project. Architect confirms whether this should be required or optional.

---

## Handoff

**Next role:** architect

The architect reads this output and the brief to:
- Define the full CONTEXT.md structure for `roles/model-trainer/`: exact Inputs table schema, Process step language, Output file template (section headers and content rules per section).
- Resolve the four open questions above — each has a proposed answer, architect confirms or overrides.
- Define the `output/output.md` template: what sections it must contain, what each section looks like when filled, what a passing vs failing run looks like.
- Define the Device/Architecture Constraints section content and format.

**Flags for architect:**
- Open question 1 (gate placement) determines whether the Process section has 5 or 6 steps — settle this before drafting the CONTEXT.md process steps.
- Open question 2 (checkpoint path convention) determines whether `output_dir` is an input field or a derived value — this affects the Inputs table schema.
- The role contract must be self-contained: someone running the role for the first time (on a new project) should be able to complete it without needing to read project 8 source code.
