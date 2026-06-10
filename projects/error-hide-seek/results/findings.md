# Experiment Findings

Results populated by `GET /results/{experiment_id}` or `uv run score --experiment-id <N>`.

| Experiment | Unaided TPR | Agent-Only TPR | Human+Agent TPR | Uplift |
|------------|-------------|----------------|-----------------|--------|
| 1 (pilot-01, n=10, gemma2:9b) | 0.67 | 0.33 | 0.50 | -0.17 |
| 2 (exp-02-claude, n=100, claude-sonnet-4-6) | pending | **0.33** | pending | pending |

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

- ~~Scale to 100 papers with claude-sonnet-4-6 as planter (subtler errors)~~ → done (exp-02)
- ~~Re-run agent_only with Claude to measure gap vs gemma2:9b~~ → done (exp-02 agent_only)
- Add time-on-task to human sessions (uplift may appear under fatigue)

---

## Experiment 2 — exp-02-claude (agent_only complete)

**Date:** 2026-06-09
**Papers:** 100 · **Errors per paper:** 1 · **Planter:** claude-sonnet-4-6 · **Blue-team:** claude-sonnet-4-6

### Results (agent_only complete; unaided + human_agent pending)

| Condition | Sessions | TPR | FPR |
|-----------|----------|-----|-----|
| unaided | 0/33 | pending | pending |
| agent_only | 33/33 | **0.33** | **0.78** |
| human_agent | 0/34 | pending | pending |

### By category (agent_only)

| Category | Planted | Detected | TPR |
|----------|---------|----------|-----|
| causal_inversion | 7 | 4 | **0.571** |
| scope_extension | 7 | 4 | **0.571** |
| inverted_conclusion | 7 | 2 | 0.286 |
| false_citation | 6 | 1 | 0.167 |
| number_substitution | 6 | 0 | **0.000** |

### Interpretation

**Agent-only TPR = 0.33, FPR = 0.78** — identical TPR to gemma2:9b in exp-1 despite harder planted errors and a stronger blue-team model. Capability and difficulty escalated in parallel.

**FPR improved slightly (0.83 → 0.78)** — claude-sonnet-4-6 is more precise than gemma2:9b; fewer false alarms per session, though still very noisy.

**Category breakdown reveals detection ceiling by error type:**
- `causal_inversion` and `scope_extension`: Claude catches ~57% — logical/semantic inconsistencies are legible from domain knowledge alone
- `inverted_conclusion`: 29% — conclusions are partially catchable but require knowing the paper's actual claim
- `false_citation`: 17% — citations are nearly undetectable without access to the reference list
- `number_substitution`: 0% — specific numbers are entirely unverifiable from abstract text alone

**Key asymmetry:** Claude-as-planter deliberately chose subtle mechanisms (single-word clause inversions, hedge removal, plausible-sounding citations). Claude-as-detector cannot overcome the ground-truth deficit — it has no access to what the "original" said. This is a fundamental limit, not a capability gap: even a perfect reasoner cannot catch `78% → 71%` without the original.

**Comparison to exp-1 by category:**
- gemma2:9b: caught `inverted_conclusion` (1.0), missed `causal_inversion` and `scope_extension` (0.0)
- claude-sonnet-4-6: reversed — detects `causal_inversion`/`scope_extension` better, weaker on `inverted_conclusion`
- Both models miss `number_substitution` entirely; claude adds near-miss on `false_citation`

### Next steps

- Run unaided and human_agent sessions for exp-2 (human review of 67 papers)
- Compute uplift: human_agent TPR − unaided TPR with Claude-quality hints
- Hypothesis: positive uplift expected since Claude hints have lower FPR than gemma2:9b (0.78 vs 0.83), reducing noise-injection degradation
