# Retro — toxicity-classifier-finetuned

**Role:** retro
**Sequence:** `new-project-full` (step 9)
**Date:** 2026-06-03

---

## Project

**Name:** toxicity-classifier-finetuned (project 8)
**Sequence:** `new-project-full` — all 9 steps completed in a single session
**Roles that ran:** brief → planner → architect → implementer → reviewer → retro (steps 4, 5, 7 skipped — no frontend)
**Sessions:** 1

---

## What Went Well

**1. Brief flags resolved efficiently at the planner stage**

All three brief flags (binary vs multi-label, `roberta-base` vs `roberta-large`, Colab deliverable) were resolved at the planner with proposed answers inline, per the routing.md convention. The architect confirmed or accepted them without reopening debate. This is the intended flow and it worked cleanly — no flag survived to the implementer as an unresolved question.

**2. Cross-project dependency check at the architect stage added real value**

Reading `projects/moderation-stream/moderation_stream/consumers/distilbert.py` and `roberta.py` directly confirmed the zero-shot baseline checkpoint names (`typeform/distilbert-base-uncased-mnli`, `roberta-large-mnli`) and candidate label format. Without this check, the evaluate module would have used a different zero-shot interface than project 22's live consumers, making the comparison meaningless. The routing.md flag to cross-check upstream projects at the architect stage paid off.

**3. Deferred imports handled consistently throughout**

All slow imports (`from transformers import ...`, `from datasets import ...`) are deferred inside function bodies. CLI startup is fast. The implementer notes and reviewer both handled this correctly. The tension with type annotation conventions was identified, documented, and resolved (module-level import of abstract base classes only).

**4. Reviewer Finding 1 caught a real structural fragility**

`_get_raw_test()` was a silent duplicate of the first half of `get_splits()`. It was correct at the time of writing but would silently produce wrong results if either split's parameters ever changed. The reviewer identified and resolved this in the same pass. The fix (derive raw texts from `test_ds.to_pandas()`) is cleaner and the two-path risk is eliminated.

---

## What Could Have Gone Better

**1. `accelerate` dependency not anticipated at the planning stage**

The planner spec listed `torch`, `transformers`, `datasets` as the ML stack, but did not include `accelerate`. HuggingFace `Trainer` in transformers 5.x requires `accelerate>=1.1.0` at `TrainingArguments.__init__` time — a hard dependency. This caused a test failure and a retroactive `uv add` during the implementer pass.

**Cause:** The dependency was not captured in the planner's technology stack table. The planner listed `transformers` but not its runtime dependencies.

**Prevention:** Add a note to `python-conventions.md` (or a new HuggingFace skill) that `Trainer`-based fine-tuning requires `accelerate` as an explicit dependency. The planner should always list `accelerate` alongside `transformers` when `Trainer` is in scope.

---

**2. `no_cuda` API removal not anticipated**

`TrainingArguments(no_cuda=...)` was specified in the architect output but has been removed in transformers 5.x. This caused a `TypeError` at runtime and required a code fix during the implementer pass (remove the argument; `Trainer` auto-detects device).

**Cause:** The architect spec was written against pre-5.x API knowledge. `transformers` 5.x has significant `TrainingArguments` API changes.

**Prevention:** Add a note to `python-conventions.md` (or a dedicated HuggingFace fine-tuning skill) documenting that `TrainingArguments` in transformers 5.x uses `use_cpu=True` semantics (or just Trainer auto-detection), and that `no_cuda` and `warmup_ratio` are removed. This is a specific, concrete gotcha worth capturing.

---

**3. Branch drift during implementer setup**

During `uv init` and `uv add` commands, the working directory shifted out of the git root, causing git operations to silently fall through to `main`. The feature branch commits existed but we were operating on `main`. Detected and corrected by checking `git status` before the final commit, but caused a confusing intermediate state.

**Cause:** `uv init` and `cd` into the new project directory combined with the git commands not using `-C` consistently.

**Prevention:** No routing or convention change needed — this is an environmental artefact of uv project initialisation. The `setup-uv-project.md` skill already instructs `cd /path/to/parent/; uv init ...` — the branch check at the end of the implementer pass (before commit) is the right safeguard and worked as intended.

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| Architect | Cross-referenced `moderation_stream/config.py` and both consumer files to find zero-shot checkpoint names — 3 files read for what is essentially a constant | Low | Document `ZERO_SHOT_CHECKPOINTS` in a project-level comment in `moderation_stream/config.py` or in the project 8 brief directly; architect shouldn't need to read consumer implementation files for this |
| Implementer | `skills/setup-uv-project.md` read again despite being read in previous sessions this workspace | Low | Expected — skills are stateless and short. No change. |
| Retro | All reviewer + implementer outputs in context simultaneously | Low | This is intended — retro needs both. No change. |

### Redundancy Patterns

- The four reviewer fixes (post-PASS WITH NOTES) were applied immediately in the same turn as the reviewer output. This is efficient but means the reviewer output already describes the pre-fix state. No structural redundancy in the outputs themselves.
- `asyncio_mode = "auto"` appeared in `pyproject.toml` from the workspace uv template and was never used. Minor noise removed during the reviewer pass.

### Scoping Recommendations

- The retro role instruction says "do not load language conventions files unless a specific finding requires it." Followed correctly — no python-conventions.md loaded in this role. Convention held.
- The architect stage could have been slightly lighter if the zero-shot checkpoint names were documented upstream (in the brief or project-state.md) rather than requiring a cross-project file read. Low priority.

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `resources/python-conventions.md` | Add **HuggingFace Trainer** section: (1) always add `accelerate` as an explicit dep when `Trainer` is in scope; (2) `no_cuda` removed in transformers 5.x — use Trainer auto-detection; (3) `warmup_ratio` removed in transformers 5.2 — use `warmup_steps`; (4) `eval_strategy` and `save_strategy` must match when `load_best_model_at_end=True` | Two real gotchas hit this session that a conventions note would prevent next time | No |

### Skills to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| None | — | `setup-uv-project.md` held up correctly. No changes needed. | — |

### Routing Changes

| Sequence | Change | Reason | Human decision required? |
|----------|--------|--------|--------------------------|
| None | — | `new-project-full` ran cleanly. Steps 4–5 (design-brief, frontend-architect) correctly skipped for a Python-only project. | — |

### New Resources or Skills Needed

None required. The HuggingFace conventions note (above) is additive to `python-conventions.md` and does not warrant a new file.

---

## One Change to Make Now

**Add a HuggingFace Trainer section to `resources/python-conventions.md`.**

Append the following block to the end of that file:

```markdown
## HuggingFace Trainer (fine-tuning projects)

- Always add `accelerate` as an **explicit** dependency when `Trainer` is in scope. It is a hard runtime dep of `transformers.Trainer` in versions ≥5.x and is not auto-installed.
- `no_cuda` was removed in transformers 5.x. Use Trainer auto-detection (MPS → CUDA → CPU). Do not pass `no_cuda` to `TrainingArguments`.
- `warmup_ratio` was removed in transformers 5.2. Use `warmup_steps` (integer) instead.
- `eval_strategy` and `save_strategy` must use the same value (e.g. both `"epoch"`) when `load_best_model_at_end=True`. Mismatched values raise a config error at `Trainer.__init__`.
- Deferred imports inside `train()` function bodies are correct for slow HuggingFace loads. Patch at `transformers.AutoModelForSequenceClassification.from_pretrained` (the source), not at the module-level name (which doesn't exist for deferred imports).
```

This directly prevents the two real failures hit this session (`accelerate` missing, `no_cuda` error) and the test-patching confusion on the first attempt. High value, zero risk, takes 2 minutes to apply.

---

## Handoff

This output is for human review. After sign-off:

1. **Apply the One Change:** append the HuggingFace Trainer block to `resources/python-conventions.md`.
2. **Update `_config/project-state.md`:** mark `new-project-full` complete for project 8; set next action to retro recommendations applied + Hostinger deploy.
3. **Merge `project-8-toxicity-classifier` into `main`** once deploy is ready (or keep on branch until weights are produced and project 22 Phase 2 can be tested end-to-end).
