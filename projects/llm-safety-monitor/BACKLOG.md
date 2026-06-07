# llm-safety-monitor — Backlog

## UI

### Add Model Disagreement tab
**Endpoint:** `GET /metrics/disagreements` (already implemented)
**What it shows:** Events where pair classifier and taxonomy classifier contradict each other.
- pair_classifier predicts safe but taxonomy flags a harm category → model missed a real signal
- pair_classifier predicts unsafe but taxonomy shows no harm category → false alarm

**Tab content:**
- Total disagreement count + rate (disagreements / total events)
- Scrollable sample table: event_id, prompt snippet, pair_label, taxonomy_labels
- Consider adding a timeseries line: disagreement rate over time (bucket by hour)

**Also add to this tab or a companion Metrics tab:**
- `/metrics/calibration` — reliability diagrams per model (confidence vs actual positive rate)
- `/metrics/timeseries` — F1/precision/recall over time per model (already has the data, just needs a chart)

**Routing suggestion:** Add "Disagreements" as a 5th tab in `App.tsx` alongside StreamMonitor, ModelPerformance, TaxonomyTrends, HumanReview.

---

## Known Issues

### F1 metrics are computed against producer ground-truth labels, not a held-out test set
- HH-RLHF `chosen` responses are labeled `ground_truth_safe=True` in bulk, even when the conversation discusses harmful topics. This inflates false positive counts for the pair classifier.
- The pair classifier's production F1 (~0.03) reflects this label noise, not the model's true discriminative ability (training eval F1=0.549 on a proper held-out split).
- Longer term: add a `source_dataset=wildguard` filter to `/metrics` so F1 is computed only on WildGuard data where harm labels are reliable.
