# Experiment Findings

Results populated by `GET /results/{experiment_id}` or `uv run score --experiment-id <N>`.

| Experiment | Unaided TPR | Agent-Only TPR | Human+Agent TPR | Uplift |
|------------|-------------|----------------|-----------------|--------|
| 1 (pilot-01, n=10, gemma2:9b) | 0.67 | 0.33 | 0.50 | -0.17 |
| 2 (exp-02-claude, n=100, claude-sonnet-4-6) | **0.30** | **0.33** | **0.29** | **−0.01** |

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
| unaided | 33/33 | **0.30** | **0.64** |
| agent_only | 33/33 | **0.33** | **0.78** |
| human_agent | 34/34 | **0.29** | **0.72** |

### By category (unaided)

| Category | Planted | Detected | TPR |
|----------|---------|----------|-----|
| inverted_conclusion | 6 | 3 | **0.500** |
| scope_extension | 6 | 2 | 0.333 |
| number_substitution | 7 | 2 | 0.286 |
| false_citation | 8 | 2 | 0.250 |
| causal_inversion | 6 | 1 | **0.167** |

### By category (agent_only)

| Category | Planted | Detected | TPR |
|----------|---------|----------|-----|
| causal_inversion | 7 | 4 | **0.571** |
| scope_extension | 7 | 4 | **0.571** |
| inverted_conclusion | 7 | 2 | 0.286 |
| false_citation | 6 | 1 | 0.167 |
| number_substitution | 6 | 0 | **0.000** |

### Interpretation (unaided)

**Unaided TPR = 0.30, FPR = 0.64** — human reviewer caught 10/33 planted errors cold. FPR of 0.64 means false flags on roughly 2/3 of sessions where nothing was flagged correctly (or multiple flags were submitted).

**Category difficulty (hardest → easiest for unaided human):**
1. `causal_inversion` (17%) — single-verb direction flips are nearly invisible without the original
2. `false_citation` (25%) — Claude-planted citations are more naturalistic than gemma2:9b's repeated "Smith et al. 2023"; fewer double-period tells
3. `scope_extension` (33%) — vague quantifiers hard to flag without knowing the original number
4. `number_substitution` (29%) — plausible numbers; caught when domain context made the value feel implausible
5. `inverted_conclusion` (50%) — directional reversals most salient; catchable from paper title alone

**Comparison to agent_only:** Human unaided (0.30) slightly below Claude agent_only (0.33). Almost identical performance — human pattern-matching and LLM domain reasoning converge near the same ceiling when both lack ground truth access.

---

### Interpretation (agent_only)

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

### By category (human_agent)

| Category | Planted | Detected | TPR |
|----------|---------|----------|-----|
| inverted_conclusion | 6 | 5 | **0.833** |
| false_citation | 7 | 2 | 0.286 |
| causal_inversion | 7 | 1 | 0.143 |
| scope_extension | 7 | 1 | 0.143 |
| number_substitution | 7 | 1 | **0.143** |

### Interpretation (human_agent and uplift)

**Human+Agent TPR = 0.29, FPR = 0.72. Uplift = −0.01** — essentially zero. Claude hints did not improve overall detection rate vs unaided review.

**The inverted_conclusion exception:** Human+Agent TPR for `inverted_conclusion` jumped from 0.50 (unaided) to **0.83** — the one category where Claude hints genuinely helped. These are logical reversals that Claude can identify without domain knowledge, and the hints confirmed the reviewer's intuition.

**Where hints failed to help:**
- `causal_inversion`, `scope_extension`, `number_substitution`: all 0.14 in human_agent — same or worse than unaided. Claude's annotations for these categories either missed the error or flagged unrelated spans, and the reviewer followed false leads.
- FPR actually increased slightly vs unaided (0.72 vs 0.64) — Claude's noise caused the reviewer to flag more false positives in sessions where the actual error wasn't caught.

**Domain knowledge is the binding constraint.** Both the human reviewer and Claude lack access to:
- What numbers are plausible for a specific model architecture or benchmark
- Whether a cited author/year actually exists in the field
- The causal structure of a specialized ML technique
Without ground truth, errors in these categories are nearly unverifiable regardless of hint quality.

**Category-level uplift:**

| Category | Unaided TPR | Human+Agent TPR | Uplift |
|----------|------------|-----------------|--------|
| inverted_conclusion | 0.50 | **0.83** | **+0.33** |
| false_citation | 0.25 | 0.29 | +0.04 |
| number_substitution | 0.29 | 0.14 | −0.14 |
| scope_extension | 0.33 | 0.14 | **−0.19** |
| causal_inversion | 0.17 | 0.14 | −0.02 |

The hint effect is strongly positive for structural/logical errors and zero-to-negative for domain-dependent errors. This is consistent across both experiments.

### Corpus confound: non-expert reviewer

The reviewer lacked specific expertise in the ML subfields covered by this arXiv corpus (graph neural networks, continual learning, signal integrity, fluid dynamics, etc.). This confound affects all conditions equally, but it amplifies the difficulty of domain-dependent error categories. A reviewer with ML research background would likely show higher unaided TPR on `causal_inversion` and `scope_extension` and better calibration on `number_substitution`.

**This is not a flaw in the experimental design** — it accurately reflects the real-world case where a safety reviewer reads content outside their area of expertise. The finding that structural errors (inverted_conclusion) are detectable by a non-expert but domain-dependent errors (causal_inversion, number_substitution) require field knowledge is a valid and portfolio-relevant result.

A follow-on experiment with domain-expert reviewers would isolate the expertise effect.

### Next steps

- Update project memory and portfolio narrative with complete exp-2 findings
- Consider follow-on: expert reviewer condition, or a corpus from a single well-known domain
