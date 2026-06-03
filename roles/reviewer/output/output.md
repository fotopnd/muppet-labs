# Reviewer Output — model-trainer

**Role:** reviewer
**Sequence:** `new-project-full` (step 8)
**Date:** 2026-06-03

---

## Summary

The role contract is well-structured, concise, and correctly generic — `dataset_env_var` is the key design move that decouples the role from any specific project. Two warnings: step 1.3 leaves the env var validation check underspecified, and the process has no guidance for mid-run training failures. Both are addressable with Notes additions, no restructuring required. No blocking issues.

---

## Correctness

**1. Step 1.3 — env var check is underspecified** *(warning)*
`CONTEXT.md` line 44: "Confirm `<dataset_env_var>` in `.env` resolves to `dataset_path`" states what to confirm but not how. An agent executing this will improvise. Should specify the check explicitly, e.g.:
```
grep "^<dataset_env_var>=" <project_dir>/.env
```
Then compare the extracted value to `dataset_path`. Without this, two failure modes are silently undiscoverable: the var is absent from `.env`, or it is present with a different path (stale from a prior run).

**2. No failure handling for mid-run training or evaluation** *(warning)*
The process specifies a hard stop on prerequisite failures (step 1 → gate) but says nothing about what the role should do if `uv run train` or `uv run evaluate` fails mid-execution. Training failures (OOM, numerical instability, missing dep) are realistic. The process should specify: on training or eval failure, write the model's output section with available partial data, set Session Summary status to `failed`, and stop. Without this, the role's behaviour on failure is undefined — the Session Summary `Status` column exists but the process never says when to write `failed` vs `complete`.

**3. `--max-train-samples 20000` hardcoded in smoke run** *(minor)*
`CONTEXT.md` line 51. Datasets with fewer than 20,000 samples will silently run the full dataset during the smoke run (most CLI implementations cap or ignore the flag). Not a failure, but the smoke run's fast-fail guarantee disappears. Worth a Note: if the target dataset is smaller than 20,000 samples, the smoke run uses the full dataset and wall time estimates are accurate rather than conservative.

---

## Style

The contract follows the standard six-section role contract format with Device/Architecture Constraints correctly positioned before Process. Section ordering, heading levels, and table structure are consistent with other role contracts in the workspace. No style issues.

---

## Tests

Not applicable — deliverable is a Markdown role contract with no executable code.

---

## Refactor Candidates

**`models[].field` notation in the Inputs table** — the array sub-field rows (`models[].key`, `models[].epochs`, etc.) read awkwardly as a flat table. A future pass could split the Inputs table into two: a top-level fields table and a Model Entry sub-fields table with its own header. No functional impact; cosmetic clarity improvement.

**`smoke_max_samples` as a configurable input** — hardcoding 20,000 in the smoke run command makes the field invisible to the caller. Exposing it as an optional input field (default: 20,000) would make the smoke run's parameters explicit and allow small-dataset projects to set a lower value. Low priority but aligns with the role's stated goal of being project-agnostic.

---

## Verdict

**PASS WITH NOTES** — no blocking issues. The two warnings are additive: both can be resolved by appending two bullet points to the Notes section of `CONTEXT.md`. No restructuring needed.

---

## Handoff

No next implementation role required. Recommended: apply the two warning fixes directly to `roles/model-trainer/CONTEXT.md` before proceeding to retro:

1. **Step 1.3:** replace the current check description with: `Run grep "^<dataset_env_var>=" <project_dir>/.env and confirm the value matches dataset_path. If the var is absent or the path differs, hard stop.`
2. **Notes section:** add: `If uv run train or uv run evaluate fails, write the model's output section with whatever data is available, set the Session Summary status to failed, and stop. Do not proceed to the next model.`
3. **Notes section:** add the `--max-train-samples` caveat for small datasets.
