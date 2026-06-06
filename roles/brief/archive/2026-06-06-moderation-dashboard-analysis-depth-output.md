# Brief Output — moderation-dashboard analysis depth

**Date:** 2026-06-06
**Sequence:** add-feature
**Role executing:** brief

---

## Project Name

moderation-dashboard-analysis-depth

## Description

Refactor the moderation-dashboard's analytical layer to surface three genuine safety insights from the data already being collected: classifier calibration on seeded data, confidence-distribution divergence between seeded and live traffic as a distribution-shift signal, and disagreement characterization by confidence band rather than random sampling.

## Language(s)

TypeScript (React frontend) + Python (new and modified API endpoints)

## Context and Motivation

The adversarial portfolio review on 2026-06-06 established that the current dashboard is technically strong but analytically shallow. All the right data is being collected. The wrong questions are being asked about it. The three additions in this brief transform the project from "I built a streaming dashboard" to "I built a system that measures how toxicity classifiers degrade under domain shift" — which is a Safeguards story.

The existing seeded data (30k rows with Jigsaw ground truth and `correct` column) and live data (45k+ rows without ground truth, `correct=NULL`) are both in Postgres. No new data collection is needed.

## Success Criteria

### Addition 1 — Calibration Analysis tab (new tab)

A new fifth tab ("Calibration") that shows, for each active model:

**Panel A — Reliability diagram (seeded data only)**
Ten confidence decile buckets (0–10%, 10–20%, … 90–100%). For each bucket: the mean confidence and the actual accuracy (fraction of `correct=true` rows). A well-calibrated model plots close to the diagonal. A miscalibrated model shows systematic over- or under-confidence. Backend: `GET /metrics/calibration` returning per-model, per-decile `{ mean_confidence, accuracy, count }`.

**Panel B — Confidence distribution: seeded vs live**
For each model, a histogram overlay showing the confidence distribution on seeded rows vs live rows (`seeded=false`). Divergence between the two distributions is the distribution shift signal — a model whose confidence distribution shifts significantly on live data has learned training-set-specific features rather than generalizable signal. Backend: same endpoint, additional `confidence_distributions` field with bucket counts.

**Panel C — Agreement-confidence correlation (live data only)**
For each confidence decile on live data, the inter-model agreement rate (fraction of events in that decile where all three models agree on the label). High-confidence predictions that have low inter-model agreement are the calibration failure signal — the model is confidently wrong relative to its peers. Backend: same endpoint, `agreement_by_confidence` field.

**The tab must include one framed insight sentence per model**, not just charts. Example: *"DistilBERT zero-shot is well-calibrated on Jigsaw data (reliability curve R²=0.94) but shifts its confidence distribution rightward on live Bluesky, producing high-confidence predictions that other models disagree with at 2.3× the seeded rate."* These sentences are computed, not hardcoded.

### Addition 2 — Distribution shift narrative on ModelPerformance and ModelCard

Replace the current "Live flag rate: X.X%" stat with a framed two-line display:

```
Live flag rate    38.6%
vs eval baseline  ↑3.4× (Jigsaw test: 11.4% positive rate)
```

The baseline comparison is the positive rate of the Jigsaw test set (fixed constant: ~11.4% toxic in the Jigsaw dataset). The multiplier `38.6 / 11.4 = 3.4×` is the distribution shift indicator. A model with a multiplier close to 1.0 is generalizing. A model with 3.4× is over-flagging on live content relative to its training distribution.

This requires no new backend endpoint — it is a frontend-only change using the existing `live_event_count` and `live_flagged_count` fields. The Jigsaw baseline positive rate is a known constant embedded in the frontend config.

### Addition 3 — Disagreement characterization by confidence band

Replace the current random sample list in DisagreementPanel with:

**Confidence band breakdown table**
For model disagreements, group by confidence profile:
- `both-uncertain` — both dissenting models have confidence < 0.6
- `split-confidence` — one model high confidence (> 0.7), one low (< 0.5)
- `both-confident` — both dissenting models have confidence > 0.7

The count and percentage in each band. `both-confident` disagreements are the most dangerous (two models confidently disagree) and should be highlighted.

**One framed insight sentence**: *"X% of disagreements are split-confidence (one model certain, one uncertain), suggesting the dissenting model is operating near its decision boundary on this content type."*

**Retain the sample posts**, but sort them by confidence band (both-confident first) rather than showing random samples. This makes the samples illustrative of the analysis rather than decorative.

Backend: extend `GET /metrics/disagreements` with a `by_confidence_band` field.

## Constraints

- No new data collection — all analysis runs on existing `classifications` and `escalations` tables
- No model retraining or threshold changes
- `correct` is NULL for live rows — all accuracy calculations must filter to `seeded=true` rows
- Calibration endpoint must be fast enough for a 3-second frontend poll — use pre-aggregated SQL, not row-level Python computation
- The framed insight sentences must be generated from real computed values, not hardcoded strings
- Must not break any existing tests

## Out of Scope

- Annotation bias audit
- Adversarial input detection or red-teaming
- Feedback loop from human review to classifier
- Model retraining or threshold tuning
- Calibration post-processing (Platt scaling, isotonic regression) — analysis only, not correction

## Assumptions

- The Jigsaw test set positive rate (~11.4% toxic) is a stable constant usable as a baseline. Planner should confirm this is the right reference point or propose an alternative.
- Inter-model agreement as a proxy for calibration quality on live data is methodologically valid given the absence of ground truth labels. This is a stated assumption in the UI, not a hidden claim.
- The calibration SQL can group by `confidence` decile via `FLOOR(confidence * 10) / 10` without a materialized view — planner to assess query performance at ~50k rows.
- The insight sentences can be generated by a simple Python function that reads the computed values and selects from a small set of templates. No LLM call needed.

## Open Questions for Planner

1. Does the Calibration tab warrant its own route (`/calibration`) or should it live as a new panel within an existing tab? Given its analytical weight, a dedicated tab is probably correct.
2. Should `GET /metrics/calibration` be a single merged endpoint or split into `/metrics/calibration/reliability`, `/metrics/calibration/distributions`, `/metrics/calibration/agreement`? One endpoint simplifies the frontend but may be slow; split endpoints allow progressive loading.
3. The insight sentence generation: template-based Python function in the backend (returned as a string field in the API response) vs computed in the frontend from raw values? Backend is cleaner for testing; frontend gives more flexibility.

## Handoff

Next role: planner

Reads this file plus `_config/project-state.md`.

The planner should:
1. Resolve the three open questions above
2. Confirm SQL feasibility for calibration queries at current data volume
3. Map exactly which files are new vs modified (the calibration tab is new; ModelCard and DisagreementPanel are modifications)
4. Assess whether the insight sentence logic belongs in backend or frontend
