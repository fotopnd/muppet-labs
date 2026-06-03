# Implementer Output — model-trainer

**Role:** implementer
**Sequence:** `new-project-full` (step 6)
**Date:** 2026-06-03

---

## Files Produced

| File | Purpose |
|------|---------|
| `roles/model-trainer/CONTEXT.md` | Role contract: Identity, Inputs, Device/Architecture Constraints, Process, Output, Notes |
| `roles/model-trainer/output/output.md` | Blank output template showing all required sections |

---

## Setup Steps Taken

None — no project directory initialisation required. The role is a Markdown deliverable, not a software project.

---

## Deviations from Architecture

None.

---

## Known Gaps

None. The role contract is fully specified per the architect output. Future invocations of the role will fill in `output/output.md` at runtime — the blank template is intentional.

---

## How to Run

To invoke the model-trainer role, read `roles/model-trainer/CONTEXT.md` and supply the required Inputs:

```
project_dir: /absolute/path/to/project
dataset_path: /absolute/path/to/data.csv
dataset_env_var: MY_DATA_DIR
models:
  - key: distilbert
    epochs: 4
    batch_size: 32
    baseline_checkpoint: distilbert-base-uncased  # optional
```

The role validates prerequisites, runs smoke → full → evaluate for each model in order, and writes results to `roles/model-trainer/output/output.md`.

---

## Handoff

**Next role:** reviewer

The reviewer should assess:
- Whether the CONTEXT.md follows the standard role contract format (six sections, correct ordering of Device/Architecture Constraints before Process)
- Whether the Inputs table is complete and unambiguous (especially `dataset_env_var` — the key generalisation)
- Whether the Process steps are self-contained: could someone invoke this role for the first time on an unfamiliar project and complete it without reading project 8 source code?
- Whether the output template correctly reflects the Output section schema in CONTEXT.md
