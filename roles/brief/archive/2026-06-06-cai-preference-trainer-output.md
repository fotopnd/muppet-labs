# Brief Output — cai-preference-trainer

**Role:** brief
**Sequence:** `new-project-full` (step 1)
**Date:** 2026-06-06

---

## Project Name

`cai-preference-trainer`

---

## Description

A mini Constitutional AI pipeline — annotation UI, preference dataset builder, DistilBERT reward model trainer, and per-principle evaluation dashboard — demonstrating RLHF preference learning directly referenced to Anthropic's Constitutional AI methodology.

---

## Language(s)

- **Backend:** Python 3.12 (uv, FastAPI, SQLAlchemy, Pydantic v2, HuggingFace Trainer)
- **Frontend:** TypeScript (React 18, TanStack Query, shadcn/ui, recharts)
- **Package managers:** uv (Python), pnpm (TypeScript)
- **Formatting/linting:** ruff (Python), prettier + eslint (TypeScript)
- **Database:** PostgreSQL 16 (port 5436)

---

## Success Criteria

The project is done when all of the following are true:

1. **Response pair ingestion** — HH-RLHF dataset loads from HuggingFace (`Anthropic/hh-rlhf`) and persists chosen/rejected pairs to `response_pairs` table; Ollama pair generator CLI produces additional pairs (T=0.2 vs T=0.9) from user-supplied prompts and persists them alongside HH-RLHF pairs.
2. **Annotation UI** — annotator can open `/annotate`, view a pair (prompt + response A + response B), select A/B/Tie per each of the 10 CAI principles, set optional confidence (1–3), and submit; submission persists to `annotations` table with `annotator_id`, `pair_id`, `principle_id`, `preferred`, `confidence`, `annotated_at`.
3. **Annotation queue** — Annotation Queue tab lists all unannotated pairs (pairs with fewer than 10 principle annotations); annotated pairs no longer appear in the queue.
4. **Reward model training CLI** — `uv run train-rm` in `cai-preference-trainer/` trains a single DistilBERT binary classifier; principle identity is encoded as "Principle N: [text]" prepended to input text; training runs on MPS and produces a checkpoint saved via `model.save_pretrained()`.
5. **Per-principle evaluation** — `uv run evaluate-rm` computes accuracy and AUC-ROC per principle (filtered from held-out 20% annotations); outputs a JSON eval file to `resources/evals/cai-preference-trainer/`.
6. **Calibration** — 10-bin equal-width calibration computed per principle from eval output; CalibrationChart renders probability vs fraction positives in the Calibration dashboard tab.
7. **Dashboard — 4 tabs** — Annotation Queue (unannotated pair list), Principle Coverage (annotation count + agreement rate per principle), RM Eval (accuracy/AUC per principle, model card), Calibration (CalibrationChart per principle).
8. **Tests** — pytest tests covering: HH-RLHF pair loader, annotation submit/fetch endpoints (seeded DB), RM dataset builder, calibration bin computation.

---

## Constraints

- **Apple M4 24 GB (MPS):** training hardware is local Mac; no CUDA. MPS used via HuggingFace Trainer auto-detection; `bf16` not passed (MPS constraint).
- **No Kafka:** synchronous annotation submission; one-shot training CLI — no streaming pipeline.
- **Postgres on port 5436:** non-default port; matches workspace convention.
- **DistilBERT only:** `distilbert-base-uncased` as the reward model base; no multi-model comparison.
- **No production deployment in v1:** runs locally; no VPS, no Docker in scope.
- **10 CAI principles fixed:** the exact 10 principles from Anthropic's HH-RLHF card are hardcoded as a static list — no admin UI for managing principles.
- **Minimum annotation threshold:** RM training requires at least 50 non-TIE annotations total before training makes sense (architect to confirm).

---

## Out of Scope

- PPO or any RL training loop (reward model only — not the full RLHF loop)
- Multi-annotator agreement metrics (e.g. Cohen's kappa) — agreement rate (% non-TIE) is sufficient for v1
- Active learning or smart pair selection — pairs are presented in creation order
- Model serving / inference API for the trained reward model
- Annotator authentication — `annotator_id` is a free-text field; no login system
- Hyperparameter search for RM training
- Automated retraining on new annotations — training is a manually triggered CLI command

---

## Assumptions

1. **Single RM with principle prefix** — one DistilBERT model trained on all annotations; principle identity encoded as "Principle N: [text]" prepended to input. Simpler than 10 separate models; planner confirms.
2. **TIE annotations excluded from training** — only A-preferred and B-preferred annotations become training examples. TIEs are stored but not used. Label: 0 = A preferred, 1 = B preferred.
3. **`cai-preference-trainer/` is a separate uv project** — same pattern as `llm-safety-monitor-training/`. The FastAPI service lives in `cai-preference-trainer-api/`; the trainer in `cai-preference-trainer/`.
4. **Ollama pair generation is a CLI script** — triggered manually before annotation sessions; uses `qwen2.5-coder:7b`; same prompt at T=0.2 and T=0.9 produces response_a and response_b.
5. **Annotation UI is a route in the same React app** — `/annotate` route in the same SPA as the dashboard; no separate build.
6. **HH-RLHF prompt extraction** — `chosen` field text is split on `\n\nAssistant:` to extract the human prompt; `chosen` tail is response_a; `rejected` tail is response_b for source `'hhrlhf'`.
7. **Frontend project slug:** `cai-preference-trainer-ui/` — Vite + React + TypeScript, initialised with pnpm.
8. **Calibration pattern matches llm-safety-monitor** — same 10-bin equal-width logic; same CalibrationChart visual.

---

## Handoff

**Next role:** planner

The planner reads this file to:
- Confirm or revise Assumptions 1 (single RM), 3 (separate uv project), 5 (same-app route)
- Define all functional requirements as testable statements
- Map the full top-level file and module structure for both Python projects and the frontend
- Confirm tech stack versions and key library choices
- Identify open questions for architect

**Flags for planner:**
- Assumption 2 (TIE exclusion from training) — confirm this is the right handling; alternative is a three-class model.
- Assumption 6 (HH-RLHF prompt extraction) — verify the schema against `Anthropic/hh-rlhf` on HuggingFace before architect locks in the SQL schema.
- The annotation queue definition ("pairs with fewer than 10 principle annotations") — planner should decide if a pair is "annotated" when all 10 principles have been rated, or just when any annotation exists.
