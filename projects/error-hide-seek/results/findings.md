# Experiment Findings

Results populated by `GET /results/{experiment_id}` or `uv run score --experiment-id <N>`.

| Experiment | Unaided TPR | Agent-Only TPR | Human+Agent TPR | Uplift |
|------------|-------------|----------------|-----------------|--------|
| 1 (pilot-01, n=10, gemma2:9b) | 1.00 | 0.33 | 1.00 | +0.00 |

---

## Experiment 1 — pilot-01

**Date:** 2026-06-08
**Papers:** 10 · **Errors per paper:** 1 · **LLM backend:** gemma2:9b (Ollama, local)

### Results

| Condition | Sessions | TPR | FPR |
|-----------|----------|-----|-----|
| unaided | 3/3 | **1.00** | 0.00 |
| agent_only | 3/3 | **0.33** | 0.83 |
| human_agent | 4/4 | **1.00** | 0.00 |

### By category

| Category | Unaided | Agent-only | Human+Agent |
|----------|---------|------------|-------------|
| inverted_conclusion | 1.0 | 1.0 | — |
| number_substitution | 1.0 | — | 1.0 |
| false_citation | 1.0 | — | 1.0 |
| causal_inversion | — | 0.0 | 1.0 |
| scope_extension | — | 0.0 | 1.0 |

### Interpretation

**Uplift = 0.0** — errors in this pilot were detectable enough that humans found all of
them regardless of agent assistance. Uplift will be more meaningful at scale with subtler
errors; this run confirms the measurement pipeline is correct end-to-end.

**Agent-only TPR = 0.33, FPR = 0.83** — gemma2:9b detected the `inverted_conclusion`
(explicit logical reversal) but missed `causal_inversion` and `scope_extension`. Most
flagged text was noise. Claude-class models would be expected to perform substantially
better, particularly on subtler categories.

**Category difficulty (agent perspective, hardest → easiest):**
1. `causal_inversion` — directional logic change; easy for humans, hard for weak LLMs
2. `scope_extension` — quantifier removal ("four benchmarks" → "a wide range")
3. `number_substitution` — requires domain plausibility judgment
4. `false_citation` — structural tell (double period, orphan attribution)
5. `inverted_conclusion` — explicit reversal; easiest for any reviewer

### Scorer fix applied

`is_true_positive` originally checked only against `original_text` (pre-alteration span).
Reviewers see the altered abstract, so they flag altered text. Fixed to check both
`original_text` and `altered_text`. See `error_hide_seek/scoring/scorer.py`.

### Next steps

- Scale to 100 papers with claude-sonnet-4-6 as planter (subtler errors)
- Re-run agent_only with Claude to measure gap vs gemma2:9b
- Add time-on-task to human sessions (uplift may appear under fatigue)
