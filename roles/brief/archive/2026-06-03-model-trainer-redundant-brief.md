# Brief Output — model-trainer

**Role:** brief
**Sequence:** `new-project-full` (step 1)
**Date:** 2026-06-03

---

## Project Name

model-trainer

---

## Description

A reusable workspace role that validates prerequisites, runs a fine-tuning pipeline (smoke run + full run), evaluates the resulting checkpoint, and produces a structured handoff for downstream consumers.

---

## Language(s)

Python — the role is a workspace process definition, not a standalone project. The training code it drives is Python (PyTorch / HuggingFace Transformers via uv).

---

## Success Criteria

- Role contract (`CONTEXT.md`) is written and follows the standard role contract format
- Role validates dataset path and `.env` before running anything — hard stop if missing
- Role executes in order: validate → uv sync → smoke run → full run → evaluate
- Role produces `output/output.md` containing: checkpoint paths (absolute), eval metrics table (F1, AUC-ROC, fine-tuned vs zero-shot), epoch loss curve summary, downstream wiring instructions
- Role is generic enough to be reused across model architectures — not hardcoded to DistilBERT/RoBERTa

---

## Constraints

- Must fit the existing role contract format (`roles/[role]/CONTEXT.md` + `output/output.md`)
- Smoke run is required on first execution of any new model/dataset combination; optional on reruns
- MPS device support must be accounted for: no `bf16`, no `pin_memory` warnings treated as errors, RoBERTa-class models default `--batch-size 8` on Apple Silicon
- Dataset lives in `resources/datasets/` — role must resolve absolute path and validate before training starts
- No wandb / tensorboard dependencies — `report_to="none"` always

---

## Out of Scope

- Does not implement training code — it drives existing CLI entry points (`uv run train`, `uv run evaluate`)
- Does not manage model architecture design or hyperparameter search
- Does not deploy or upload checkpoints to HuggingFace Hub or cloud storage
- Does not handle distributed training (multi-GPU, FSDP, DDP)
- Does not manage dataset download — assumes dataset is already present in `resources/datasets/`

---

## Assumptions

- **Training CLI follows the established pattern:** `uv run train --model <key> --output-dir <dir> --epochs <n>` and `uv run evaluate --model <key> --checkpoint-dir <dir>`. If a future project uses a different CLI shape, the role contract will need a project-specific override section.
- **One model at a time.** The role runs one model key per invocation. Running DistilBERT + RoBERTa in sequence requires two role invocations (or a compound invocation the human initiates).
- **Sequence used:** `new-project-full` — model-trainer is a workspace role, not a software project, but it benefits from the full sequence (brief → planner → implementer writes the CONTEXT.md).

---

## Handoff

**Next role:** planner

The planner reads this file to define:
- The role contract structure for `roles/model-trainer/CONTEXT.md`
- The exact prerequisite checklist (env validation steps)
- The process steps the role executes (with CLI commands)
- The output file structure for `roles/model-trainer/output/output.md`

**Flag for planner:** The "one model at a time vs. multi-model" question is left open. The planner should propose an answer — likely a `models:` list field in the role input section — and note it as a proposed answer for the architect to confirm.
