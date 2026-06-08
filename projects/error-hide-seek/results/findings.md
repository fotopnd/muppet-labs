# Experiment Findings

Results populated by `GET /results/{experiment_id}` or `uv run score --experiment-id <N>`.

| Experiment | Unaided TPR | Agent-Only TPR | Human+Agent TPR | Uplift |
|------------|-------------|----------------|-----------------|--------|
| 1 (pilot-01, n=10, gemma2:9b) | 0.67 | 0.33 | 0.50 | -0.17 |

---

## Experiment 1 — pilot-01

**Date:** 2026-06-08
**Papers:** 10 · **Errors per paper:** 1 · **LLM backend:** gemma2:9b (Ollama, local)

### Results

| Condition | Sessions | TPR | FPR |
|-----------|----------|-----|-----|
| unaided | 3/3 | **0.67** | 0.00 |
| agent_only | 3/3 | **0.33** | 0.83 |
| human_agent | 4/4 | **0.50** | 0.67 |

**Human uplift: −0.17** (human_agent performed worse than unaided on this pilot)

### By category

| Category | Unaided | Agent-only | Human+Agent |
|----------|---------|------------|-------------|
| inverted_conclusion | 0.0 | 1.0 | — |
| number_substitution | 1.0 | — | 1.0 |
| false_citation | 1.0 | — | 1.0 |
| causal_inversion | — | 0.0 | 0.0 |
| scope_extension | — | 0.0 | 0.0 |

### Interpretation

**Uplift = −0.17** — agent hints slightly hurt performance in this pilot. The human
reviewer correctly found `number_substitution` and `false_citation` unaided, but in the
human_agent condition the agent's noisy hints (high FPR) led to additional false
positives on sessions 14 and 15 without helping catch the actual errors. This is the
"noise injection" failure mode — agent with poor precision degrades human judgment.

**Unaided TPR = 0.67** — human caught `number_substitution` (high number felt off) and
`false_citation` (double period noticed) but missed `inverted_conclusion` (the directional
reversal in a technical sentence wasn't salient without domain context).

**Agent-only TPR = 0.33, FPR = 0.83** — gemma2:9b caught `inverted_conclusion` but
missed `causal_inversion` and `scope_extension`. High noise rate confirms this model
lacks the domain precision for reliable academic error detection.

**Hardest categories (neither human nor weak LLM detected):**
- `causal_inversion` — "is maintained through" → "enables" is subtle; missed by all
- `scope_extension` — "four benchmarks" → "a wide range" requires knowing the original

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
