# Error Hide and Seek

A randomised controlled trial platform measuring whether an AI detection agent improves humans' ability to spot planted errors in scientific abstracts — and how that uplift varies across five error categories.

---

## Research question

> When a blue-team agent (Claude Sonnet 4.6) annotates an abstract before a human reviewer reads it, does human detection rate increase, and does the gain depend on error type?

This is a measurement problem, not a classification problem. The outcome variable is **True Positive Rate (TPR) uplift**: `TPR(human+agent) − TPR(unaided)`.

---

## Experimental design

Three within-corpus conditions, assigned at experiment creation:

| Condition | Description | Agent role |
|---|---|---|
| `UNAIDED` | Human reads the abstract alone | None |
| `AGENT_ONLY` | Agent auto-scores; no human review | Fully automated |
| `HUMAN_AGENT` | Agent annotates, human reviews with annotations visible | Advisory |

Papers are randomly assigned to conditions at experiment creation time using `random.Random(experiment_id)` as the seed (deterministic, reproducible for reruns). Categories are distributed in round-robin order across the shuffled paper list so each condition sees a spread of error types rather than all the same category.

The `intended_category` is stored on `experiment_papers` at creation, not computed at plant time. This decouples the plant-errors step from condition assignment and prevents the two from drifting out of sync if the DB query order changes.

---

## Error taxonomy

Five categories of plausible, non-obvious errors that a competent reviewer might miss:

| Category | Description |
|---|---|
| `inverted_conclusion` | Claim direction reversed (e.g., "improves" → "degrades") |
| `number_substitution` | A reported figure changed (percentage, sample size, p-value) |
| `false_citation` | A cited method or paper replaced with a plausible but wrong reference |
| `scope_extension` | Findings overgeneralised to a broader population than the study covered |
| `causal_inversion` | A correlational finding restated as a causal claim |

Categories were chosen to represent distinct cognitive failure modes — pattern-matching on syntax vs semantic understanding vs factual recall — so that per-category TPR differences are informative about what the agent is actually good at.

---

## Pipeline

```
fetch-corpus ──► papers ──► create_experiment ──► experiment_papers
                                                         │ (intended_category, condition)
                                                         ▼
                                               plant-errors (Red-team Claude)
                                                         │ (altered_abstract, original_text)
                                                         ▼
                                               POST /sessions ──► Blue-team Claude
                                                         │ (annotations + confidence)
                                                         ▼
                                               Human review (UNAIDED / HUMAN_AGENT)
                                               Auto-score  (AGENT_ONLY)
                                                         ▼
                                               GET /results/{experiment_id}
```

### Red-team agent (plant-errors)

Calls `claude-sonnet-4-6` with a structured prompt asking it to identify one falsifiable claim and produce an altered version with a rationale. Output is a JSON object with `original_text`, `altered_text`, `rationale`. Two-attempt retry on parse failure; raises on double failure.

### Blue-team agent (annotate)

Same model, different system prompt. Asked to return a JSON array of suspicious text excerpts with `confidence` (`"high"/"medium"/"low"`) and `reason`. Confidence is a string enum — the production scoring path filters on `confidence == "low"`, not on a numeric threshold.

#### Low-confidence filtering in AGENT_ONLY

In `AGENT_ONLY`, annotations with `confidence == "low"` are excluded before auto-scoring. This matters because the agent sometimes flags common-but-unremarkable phrases at low confidence — including them would inflate false positive counts and make the agent-only TPR appear lower than it is against the hard cases. The human-agent condition shows all annotations, including low-confidence ones, to let the human decide.

#### Parse failure telemetry

`review_sessions.parse_failures` records how many JSON decode failures occurred across both annotation attempts. `agent_run_status` records the outcome: `success`, `parse_failed` (both attempts failed), or `skipped` (UNAIDED). This makes it possible to distinguish "agent ran and found nothing" from "agent failed to produce valid output" when aggregating TPR.

---

## Scoring

### True Positive detection

`is_true_positive(excerpt, original_text)` checks substring containment in both directions:

```python
d = excerpt.lower().strip()
p = original_text.lower().strip()
return d in p or p in d
```

The planted error was made by replacing `original_text` with `altered_text` in the abstract. A reviewer seeing the altered abstract who flags the region (even using the original phrasing to describe what looks wrong) will produce an excerpt that overlaps with `original_text`. This avoids requiring exact string match on the altered text.

### Uplift

```
uplift = TPR(human_agent) − TPR(unaided)
```

Computed per experiment. `GET /results/{experiment_id}` also returns per-category breakdown — this is where the research question gets answered: if `inverted_conclusion` shows high uplift but `number_substitution` shows near-zero, it suggests the agent is better at spotting semantic inversions than factual errors.

---

## Schema decisions

### Why `intended_category` on `experiment_papers`, not computed in `plant.py`

The original `plant.py` used `CATEGORY_CYCLE[idx % 5]` where `idx` was the enumeration index of the DB query result. This had two failure modes:

1. If the query order changed (e.g., a different ORDER BY or a vacuum that changed physical row order), the same paper could get a different category on a re-run.
2. The condition assignment and category assignment were fully independent, so you could get an experiment where all UNAIDED papers got `inverted_conclusion` and all HUMAN_AGENT papers got `causal_inversion` — making the per-condition category breakdown non-comparable.

Storing `intended_category` at creation time (from the same seeded shuffle) fixes both: the assignment is deterministic and condition-stratified by construction.

### `agent_run_status` and `parse_failures`

These exist for operational visibility, not just for debugging. An experiment with 20% `parse_failed` sessions has unreliable AGENT_ONLY results — the agent's TPR is artificially low because it produced no annotations for many papers. Surfacing this in the results endpoint makes the data quality immediately visible rather than buried in logs.

---

## Stack

| Layer | Technology |
|---|---|
| LLM (plant + annotate) | Anthropic API (claude-sonnet-4-6) |
| Paper corpus | arXiv API (cs.AI, cs.CL, cs.LG) |
| Storage | Postgres 16 + SQLAlchemy async |
| Migrations | Alembic |
| API | FastAPI + uvicorn |
| Frontend | React + Recharts |
| Language | Python 3.12 + TypeScript 5 |
