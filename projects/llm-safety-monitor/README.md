# LLM Safety Monitor

A streaming safety classification platform that processes live LLM interactions through a multi-model pipeline, stores results with full measurement provenance, and surfaces disagreements and calibration signals to human reviewers.

---

## Architecture

```
Producer ──► Kafka topic ──► pair_classifier     ──┐
                          ──► prompt_detector     ──┼──► Postgres ──► FastAPI ──► React dashboard
                          ──► taxonomy_classifier ──┘
```

The producer ingests WildGuard, HH-RLHF, and AdvBench datasets (plus live and red-team sources) and publishes `LLMInteractionEvent` JSON to a single Kafka topic. Three consumers run in parallel shadow mode — each writes a `classification_results` row without blocking the others. The FastAPI layer aggregates across classifiers to compute metrics, surface disagreements, and drive the review queue.

### Why Kafka over a request/response classifier API

Shadow mode: the monitor sits beside the real inference path rather than in it. A failed classifier does not degrade latency for users. The topic also decouples the red-team platform's attack sweep from the monitor — results flow in via an outbox publisher rather than direct DB writes.

---

## Key design decisions

### Atomic Kafka publishing with the outbox pattern

Direct Postgres + Kafka writes are not atomic: a crash between the DB commit and the Kafka publish leaves an event in the DB but missing from consumers. The outbox pattern fixes this:

1. Producer writes `interactions` row and `synthetic_events_outbox` row in the same transaction.
2. A background publisher polls for `WHERE published_at IS NULL FOR UPDATE SKIP LOCKED`, publishes to Kafka, then marks `published_at`.
3. Monitor consumers are idempotent: `UNIQUE(event_id, model_name, classifier_version)` + `IntegrityError` catch means duplicate delivery is safe.

### Classifier versioning

Every `classification_results` row carries a `classifier_version` column (short git SHA of the `llm-safety-classifier` package). This makes it possible to isolate metric regressions to a specific model update without backfilling. Legacy rows before versioning was added get `'legacy'`.

The migration (`004_add_classifier_version.py`) handles the existing-data case in three steps: add nullable, backfill `'legacy'`, dedup rows with `DISTINCT ON (event_id, model_name) ORDER BY processed_at DESC`, then `SET NOT NULL` and add the unique constraint.

### Source dataset filter on all metrics endpoints

WildGuard labels are reliable (harm categories are expert-curated). HH-RLHF labels are noisy — `chosen` responses are bulk-labeled `safe` even when the conversation touches harmful topics. All metrics endpoints default to `source_dataset=wildguard`; passing `source_dataset=all` is surfaced in the dashboard with a warning label.

This distinction matters: the pair classifier's naive F1 against HH-RLHF appears inflated (~0.7) because the majority class is easy. WildGuard-only F1 is the number worth optimising.

### Shared classifier package

Both this project and the red-team platform use the same RoBERTa-base checkpoint. Before Phase 2, they had independent preprocessing paths — the red-team was scoring `response_text` alone, while this project scored `prompt [SEP] response`. That input mismatch meant the pair classifier in the monitor and the one in the red-team were effectively different models on different distributions, making cross-project ASR comparisons meaningless.

Extracting `llm-safety-classifier` as a shared editable package (`packages/llm-safety-classifier/`) with a single `build_input_text(prompt, response)` function removes the divergence. The golden tests in that package pin the `[SEP]` concatenation contract — if either project drifts, a test fails.

---

## Measurement methodology

### F1, precision, recall

Computed against `ground_truth_safe` labels from the source dataset. Only events with a non-null ground truth contribute. Default view: WildGuard only. The `/metrics` timeseries endpoint buckets by `processed_at` hour so you can see drift after a model redeployment.

### Calibration

`/metrics/calibration` bins confidence scores into deciles and computes the actual positive rate per bin. A well-calibrated classifier has bins lying close to the `y=x` diagonal. The reliability diagram in the dashboard uses a `ReferenceLine` from Recharts to draw that diagonal. Overconfident classifiers (clusters above the diagonal) and underconfident classifiers (clusters below) are both visible immediately.

### Model disagreements

`/metrics/disagreements` finds events where `pair_classifier` and `taxonomy_classifier` give conflicting signals — pair says safe but taxonomy flags a harm category (missed signal), or pair flags unsafe with no taxonomy support (potential false alarm). These are the highest-value events to route to human review because disagreement itself is evidence of model uncertainty.

---

## Escalation router

The escalation logic uses a 2×2 matrix on `(pair_label, taxonomy_label_count)`:

| | Taxonomy flags | No taxonomy flags |
|---|---|---|
| **Pair unsafe** | `JAILBREAK` — escalate immediately | `ADVERSARIAL_PROMPT_FLAGGED` — high priority review |
| **Pair safe** | `BENIGN_HARMFUL` — taxonomy catch | `LOG_ONLY` — routine |

`MODEL_DISAGREEMENT` fires when pair and taxonomy give conflicting confidence rather than conflicting labels.

---

## Red-team integration

When the red-team platform completes an attack session, the outbox publisher injects results into this pipeline with `source_dataset=red_team`. The monitor's consumers process them identically to live traffic. The Disagreements tab's "Red-team" source filter then shows which red-team attacks the pair classifier missed — closing the feedback loop between adversarial evaluation and production monitoring.

---

## Stack

| Layer | Technology |
|---|---|
| Streaming | Apache Kafka (Confluent) |
| Storage | Postgres 16 + SQLAlchemy async |
| Migrations | Alembic |
| API | FastAPI + uvicorn |
| Classifiers | HuggingFace Transformers (RoBERTa-base) |
| Shared inference | `llm-safety-classifier` (local editable package) |
| Frontend | React 18 + Vite + Recharts + TanStack Query |
| Language | Python 3.12 + TypeScript 5 |
