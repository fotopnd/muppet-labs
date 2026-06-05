# Planner Output — moderation-dashboard v2 additions

**Role:** planner
**Sequence:** moderation-dashboard additions (vibe mode — brief COMPLETE → planner COMPLETE → implementer NEXT)
**Date:** 2026-06-05

---

## Project

`moderation-dashboard-v2-additions` — two additions to the running moderation-dashboard:
(A) a live `POST /ingest` webhook so real content can be streamed through the pipeline
in real time; (B) a fine-tuned Detoxify model (BERT multi-label classifier on Jigsaw)
to fill the fourth model slot, completing the 2×2 zero-shot/fine-tuned × binary/multi-label
comparison matrix.

---

## Resolved Open Questions (from brief)

**Q1: Is `correct` nullable?**
No — `correct: Mapped[bool] = mapped_column(Boolean, nullable=False)`.
**Resolution:** A new Alembic migration makes `correct` nullable. ORM updated to
`Mapped[bool | None]`. Consumers set `correct = None` when `ground_truth is None`
(i.e., live webhook events with no Jigsaw label). SQL queries that use `correct` in
F1 calculations already use `CASE WHEN` guards — confirm these tolerate `NULL` rows
(PostgreSQL: `correct = true` evaluates to NULL for NULL rows, which is safe for SUM).

**Q2: Does seed-sim multi-label branch work for `finetuned_detoxify`?**
No — the existing `finetuned_*` branch uses `pipeline("text-classification")` which
expects a single-label head and returns a winner label. For a 6-label sigmoid model,
this returns the top-scoring LABEL_N, not the toxic probability. A dedicated branch
is needed that loads `AutoModelForSequenceClassification` directly and reads `logits[0, 0]`
(the toxic label's raw logit).

---

## Requirements

### Workstream A — Webhook /ingest

1. `POST /ingest` accepts `{"text": "some content"}` and returns `{"event_id": "<uuid4>"}` within 100ms (Kafka publish is async; no consumer wait).
2. The published Kafka message is a valid `ModerationEvent` with `ground_truth=None`, `category="unknown"`, `jigsaw_id=-1`. All active consumers pick it up and write a `Classification` row with `correct=None`.
3. The StreamMonitor event rate counter increments within the next 3s poll cycle after a `POST /ingest`.
4. `POST /ingest` is CORS-enabled (same `allow_origins` as existing endpoints).
5. A `scripts/demo_stream.py --rate N` script POSTs one event per `1/N` seconds using synthetic content drawn from the Jigsaw CSV, running until SIGINT. Default rate: 3/s.
6. The Kafka producer used by `/ingest` is a module-level singleton initialised at first request; it is independent of all consumer-side producers.
7. A new Alembic migration makes `classifications.correct` nullable (`ALTER COLUMN correct DROP NOT NULL`).
8. `ModerationEvent.ground_truth` and `ModerationEvent.category` become `int | None` and `str` (default `"unknown"`) respectively. All consumers updated to handle `ground_truth is None` → `correct = None`.

### Workstream B — Detoxify fine-tuned

9. `projects/toxicity-classifier-finetuned/train_detoxify.py` trains `bert-base-uncased` with a 6-label linear head on Jigsaw `train.csv` for 3 epochs using `BCEWithLogitsLoss`, running on MPS device. Does not OOM on M4 24GB with batch_size=32.
10. Training saves the best checkpoint (by binary toxic F1 on validation split) to `resources/models/toxicity-classifier-finetuned/detoxify-finetuned-best/` via `model.save_pretrained()`. Follows the MPS checkpoint save bug fix: `torch.mps.synchronize()` in `on_save` callback.
11. `projects/toxicity-classifier-finetuned/evaluate_detoxify.py` evaluates the checkpoint on the Jigsaw test split and writes a JSON file to `resources/evals/toxicity-classifier-finetuned/detoxify-finetuned-<timestamp>.json` with F1, precision, recall on binary toxic label.
12. A `FinetunedDetoxifyConsumer` class in `moderation_dashboard/consumers/finetuned.py` loads the 6-label model via `AutoModelForSequenceClassification.from_pretrained(checkpoint, num_labels=6)`, runs inference with direct tokenizer + forward pass (not HF pipeline), returns `(predicted_toxic: int, sigmoid(logit[0]): float)`.
13. `runner.py` maps `finetuned_detoxify` → `FinetunedDetoxifyConsumer`.
14. `seed_sim.py` adds a `finetuned_detoxify` branch that uses the same direct inference pattern as the consumer (not pipeline). Skips gracefully if `DETOXIFY_CHECKPOINT_PATH` is not set.
15. After training and `DETOXIFY_CHECKPOINT_PATH` set in `.env`, the `finetuned_detoxify` card on Model Performance tab shows `status: active` and non-null F1.

---

## Technology Stack

| Concern | Choice | Reason |
|---|---|---|
| Language | Python 3.14 (existing) | No change |
| Package manager | uv (existing) | No change |
| Formatter/linter | ruff (existing) | No change |
| Webhook Kafka client | `confluent_kafka.Producer` (existing dep) | Already installed; module-level singleton |
| Training | HuggingFace `Trainer` + `accelerate` | Same as project 8; `BCEWithLogitsLoss` via `compute_loss` override |
| Inference (finetuned_detoxify) | `AutoModelForSequenceClassification` + `AutoTokenizer`, direct forward pass | 6-label sigmoid head; HF pipeline doesn't handle multi-label correctly |
| Migration | Alembic (existing) | One new migration file |

---

## File and Module Structure

### Workstream A — new files

| File | Purpose |
|---|---|
| `moderation_dashboard/api/routers/ingest.py` | `POST /ingest` handler; publishes `ModerationEvent` to Kafka |
| `scripts/demo_stream.py` | CLI: POST synthetic events at configurable rate |
| `alembic/versions/20260605_XXXX_nullable_correct.py` | Make `classifications.correct` nullable |

### Workstream A — modified files

| File | Change |
|---|---|
| `moderation_dashboard/types.py` | `ground_truth: int \| None`, `category: str = "unknown"` |
| `moderation_dashboard/api/models.py` | `correct: Mapped[bool \| None]`, column `nullable=True` |
| `moderation_dashboard/api/main.py` | Register `ingest_router`; add Kafka producer to lifespan `app.state` |
| `moderation_dashboard/consumers/base.py` | `correct = (predicted == event.ground_truth) if event.ground_truth is not None else None` |
| `moderation_dashboard/api/schemas.py` | Add `IngestRequest`, `IngestResponse` |
| `moderation_dashboard/.env.example` | Document: no new vars needed for webhook (uses existing `KAFKA_*`) |

### Workstream B — new files

| File | Purpose |
|---|---|
| `projects/toxicity-classifier-finetuned/train_detoxify.py` | Training script: bert-base-uncased, 6-label BCEWithLogitsLoss, MPS |
| `projects/toxicity-classifier-finetuned/evaluate_detoxify.py` | Eval script: F1/precision/recall on Jigsaw test set, binary toxic label |

### Workstream B — modified files

| File | Change |
|---|---|
| `moderation_dashboard/consumers/finetuned.py` | Add `FinetunedDetoxifyConsumer` with direct 6-label inference |
| `moderation_dashboard/consumers/runner.py` | Map `finetuned_detoxify` → `FinetunedDetoxifyConsumer` |
| `moderation_dashboard/seed_sim.py` | Add `elif model_key == "finetuned_detoxify"` branch with direct model inference |
| `moderation_dashboard/config.py` | Rename checkpoint setting: `detoxify_checkpoint_path` already added; confirm `DETOXIFY_CHECKPOINT_PATH` env var name |
| `moderation_dashboard/.env.example` | Add `DETOXIFY_CHECKPOINT_PATH=...` commented example |
| `projects/toxicity-classifier-finetuned/pyproject.toml` | Add `train-detoxify` and `eval-detoxify` entry points |

---

## Key Design Decisions

**Webhook Kafka producer:** Module-level singleton in `ingest.py`, lazily initialised on first request using settings from `get_settings()`. `Producer.produce()` is called with `on_delivery` callback; `Producer.poll(0)` is called after each produce to flush the delivery queue without blocking.

**`ModerationEvent.ground_truth = None` for webhook rows:** Consumers currently compute `correct = (predicted_label == event.ground_truth)`. Change to: `correct = (predicted_label == event.ground_truth) if event.ground_truth is not None else None`. The `correct` column nullable migration unblocks this. The existing `_METRICS_SQL` uses `SUM(CASE WHEN predicted_label = 1 AND correct THEN 1 ELSE 0 END)` — in Postgres, `NULL AND anything` evaluates to NULL, which `SUM` skips. No SQL change needed.

**`FinetunedDetoxifyConsumer` inference pattern:**
```python
inputs = self._tokenizer(content[:512], return_tensors="pt", truncation=True, padding=True)
with torch.no_grad():
    logits = self._model(**inputs).logits   # shape [1, 6]
toxic_prob = float(torch.sigmoid(logits[0, 0]))
predicted = 1 if toxic_prob >= 0.5 else 0
return predicted, toxic_prob
```
Label index 0 = `toxic` (Jigsaw column order: toxic, severe_toxic, obscene, threat, insult, identity_hate).

**Training script pattern:** Follows project 8 (`train_roberta.py`) exactly, substituting:
- `model_name = "bert-base-uncased"`, `num_labels = 6`
- `problem_type = "multi_label_classification"` in `AutoModelForSequenceClassification.from_pretrained()` — this sets the loss to `BCEWithLogitsLoss` automatically in HF Trainer
- Labels tensor: `torch.FloatTensor` of shape `[batch, 6]` from the 6 Jigsaw label columns
- Primary metric for best-checkpoint selection: F1 on binary `toxic` label (column 0)

---

## Open Questions for Implementer

None blocking. Two things to confirm during implementation:

1. `problem_type="multi_label_classification"` in `TrainingArguments` automates `BCEWithLogitsLoss` — verify this is available in the installed transformers version before using it. Fallback: subclass `Trainer` and override `compute_loss`.

2. The `demo_stream.py` script needs content text. It can either draw lines from the Jigsaw CSV (realistic toxicity distribution) or generate synthetic strings. **Use the Jigsaw CSV** — load 200 random rows at startup, cycle through them. This keeps the StreamMonitor category distribution realistic.

---

## Handoff

**Next role:** implementer

**Implementation order:**
1. Alembic migration (`correct` nullable) — everything in Workstream A depends on this
2. `types.py` — `ground_truth: int | None`
3. `models.py` — `correct: Mapped[bool | None]`
4. `consumers/base.py` — handle `None` ground_truth
5. `api/routers/ingest.py` + register in `main.py`
6. `scripts/demo_stream.py`
7. *(pause — verify webhook works end-to-end before starting B)*
8. `train_detoxify.py` in toxicity-classifier-finetuned (run overnight if needed)
9. `evaluate_detoxify.py`
10. `consumers/finetuned.py` — add `FinetunedDetoxifyConsumer`
11. `consumers/runner.py` — register new consumer
12. `seed_sim.py` — add `finetuned_detoxify` branch
13. `.env` / `.env.example` updates

**Files the implementer must read before starting:**
- `moderation_dashboard/types.py` — understand `ModerationEvent` fields
- `moderation_dashboard/consumers/base.py` — understand how `correct` is computed today
- `moderation_dashboard/consumers/finetuned.py` — template for new consumer
- `moderation_dashboard/api/main.py` — understand lifespan for producer init
- `projects/toxicity-classifier-finetuned/train_roberta.py` — template for training script
- `resources/python-conventions.md` HuggingFace Trainer section
