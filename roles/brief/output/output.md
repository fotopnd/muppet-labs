# Brief Output — moderation-dashboard safety-signal additions

**Date:** 2026-06-05
**Sequence:** moderation-dashboard safety-signal additions (vibe mode)
**Role executing:** brief

---

## Project Name

moderation-dashboard-safety-signals

## Description

Add two UI additions to the moderation-dashboard that surface safety-relevant signals currently hidden in the database: live flag rate per model card, and a model disagreement analysis panel.

## Language(s)

TypeScript (React frontend) + Python (one new API endpoint)

## Context

This is an additive pass on an existing, fully-running project. The moderation dashboard is live at localhost:5174, classifying real Bluesky posts through three models (DistilBERT zero-shot, Detoxify, DistilBERT fine-tuned) via Kafka. The backend exposes metrics via FastAPI at localhost:8002.

The motivation is a Safeguards SWE portfolio adversarial review that surfaced two gaps:

1. The model cards show F1 from seeded in-distribution data. On live Bluesky, DistilBERT zero-shot flags **38.6%** of posts as toxic vs **11.3%** (fine-tuned) and **13.2%** (Detoxify). This distribution-shift signal — the most safety-relevant finding in the project — is invisible in the UI.
2. **274 escalations/hour** come from model disagreement. The dashboard surfaces them as a queue to drain. The content patterns where models systematically disagree are not shown anywhere.

## Success Criteria

**Addition 1 — Live flag rate on model cards**

Each of the three `ModelCard` components shows a "Live: X.X% flagged" stat. The contrast between 38.6% / 11.3% / 13.2% must be visible side-by-side without clicking anywhere.

The backend `ModelMetrics` schema needs two new fields: `live_event_count: int` and `live_flagged_count: int`. The SQL in `_METRICS_SQL` (and the merged `/metrics/all` endpoint) must populate these using `FILTER (WHERE seeded=false)` conditional aggregates. Frontend computes `live_flag_rate = live_flagged_count / live_event_count` and renders it on the card.

**Addition 2 — Disagreement analysis panel**

A new section on the ModelComparison tab (or a dedicated tab if planner decides it warrants one) showing:
- Total model disagreements in the last hour
- Breakdown by predicted category: which content types most commonly cause splits
- 5–10 sampled real posts where models gave opposite verdicts, showing truncated text (140 chars) and each model's label + confidence score

Requires a new `/metrics/disagreements` endpoint returning:
```json
{
  "total_last_hour": 274,
  "by_category": {"clean": 180, "toxic": 60, "...": "..."},
  "samples": [
    {
      "event_id": "...",
      "content": "...",
      "verdicts": [{"model": "distilbert", "label": 1, "confidence": 0.71}, ...]
    }
  ]
}
```

## Constraints

- No changes to Kafka, consumers, or DB schema
- Flag rate must use live (non-seeded) event counts only — seeded rows have `seeded=true`
- Disagreement sample text truncated to 140 chars
- Must not break existing tests or introduce TS type errors

## Out of Scope

- Model retraining based on flag rate findings
- Feedback loop from human review decisions to model
- Calibration curves or reliability diagrams
- Annotation bias audit

## Assumptions

- `_METRICS_SQL` can be extended with `COUNT(*) FILTER (WHERE seeded=false)` and `SUM(predicted_label) FILTER (WHERE seeded=false)` without restructuring the GROUP BY — planner to confirm.
- Disagreement SQL: join `escalations` to `classifications` on `event_id`, filter `escalation_reason='model_disagreement'` and `"group"='shadow'`, last hour for totals/breakdown, last 50 for sample selection.
- Planner decides: disagreement panel inside existing ModelComparison tab, or new tab?
- Fixed 10-sample window is sufficient (no pagination needed for v1).

## Key data already in DB (confirmed 2026-06-05)

| Model | Live events | Flagged | Flag rate |
|---|---|---|---|
| distilbert (zero-shot) | 16,092 | 6,208 | **38.6%** |
| finetuned_distilbert | 14,893 | 1,675 | **11.3%** |
| detoxify | 15,492 | 2,050 | **13.2%** |

Disagreements: 274/hour. Top disagreement category is "clean" (models split on posts neither confidently flags).

## Handoff

Next role: planner

Reads this file plus `_config/project-state.md` for full system context (DB schema, model registry, API structure, running services).

Key questions for planner to resolve before handing to implementer:
1. Extend `_METRICS_SQL` with `FILTER` aggregates vs a separate SQL query for live counts?
2. Disagreement panel: inside ModelComparison tab, or new tab?
3. Does `/metrics/disagreements` need pagination, or is a fixed recent-window sufficient?
