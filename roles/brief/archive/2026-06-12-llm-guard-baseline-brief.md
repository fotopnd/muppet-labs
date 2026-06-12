# Brief — Llama Guard Baseline Comparison

**Sequence:** `new-project-full` | **Role:** brief | **Step:** 1 of N  
**Date:** 2026-06-12

---

## Project Name

llm-guard-baseline

---

## Description

A one-shot evaluation script that runs Llama Guard 3 (via Ollama) and the Perspective API against the same WildGuard held-out test split used to evaluate the pair classifier, producing a side-by-side F1, precision, recall, and latency comparison table that contextualises the portfolio classifier within the published baseline landscape.

---

## Language(s)

Python (standalone eval script; no new project infrastructure needed)

---

## Success Criteria

1. `uv run compare-baselines` runs Llama Guard 3 and (optionally) Perspective API against the WildGuard held-out test split (same split used for pair classifier eval)
2. Output table shows per-model: F1, precision, recall, AUC-ROC, p50/p95 inference latency
3. Pair classifier results (already computed) are included as a row in the same table
4. Results written to `benchmarks/baseline-comparison.md`
5. The comparison is referenced in llm-safety-monitor/SUMMARY.md with honest framing (we do not need to win — contextualisation is the goal)
6. Script is idempotent and reproducible: same random seed, same test split, same results on re-run

---

## Constraints

- Llama Guard 3 accessed via Ollama (local, no API cost) — model must be pullable: `ollama pull llama-guard3`
- Perspective API is optional (requires Google API key); script runs with `--skip-perspective` flag if key absent
- Test split is the existing WildGuard held-out split from llm-safety-monitor-training — not a new dataset
- No new infrastructure — single Python script with uv, runnable from llm-safety-monitor-training project
- Results table is the entire deliverable; no dashboard, no DB writes

---

## Out of Scope

- Fine-tuning Llama Guard on the WildGuard dataset
- Comparing on HH-RLHF (label noise issue documented; WildGuard only)
- OpenAI Moderation API (requires paid key; deprioritised)
- Per-category breakdown by harm taxonomy (overall F1 comparison only in v1)
- Continuous benchmarking / CI integration

---

## Assumptions

- `llama-guard3` is available via `ollama pull` (it is — Meta released it as an Ollama model)
- The WildGuard test split is already serialised from the training run (if not, the training script must be re-run with `--save-test-split` flag)
- Llama Guard 3 inference on M4 MPS will be fast enough for 4,337 samples in reasonable time (~1–2 hrs at ~1–2s/sample)
- Honest framing: pair classifier may score lower than Llama Guard on raw F1; the portfolio argument is the ensemble + disagreement architecture, not F1 maximisation

---

## Handoff

Next role: planner  
The planner must verify: whether the WildGuard test split is already saved to disk or needs to be regenerated; whether `llama-guard3` is pullable via Ollama on M4; exact input format Llama Guard 3 expects (it uses a chat template with `[INST]` tags, different from the pair classifier's `[SEP]`-joined input). These are the main implementation risks.
