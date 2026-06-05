# Brief Output — moderation-dashboard live-stream + detoxify-finetuned

**Date:** 2026-06-05
**Sequence:** moderation-dashboard additions (vibe mode)
**Role executing:** brief

---

## Project Name

moderation-dashboard-v2-additions

## Description

Two parallel additions to the existing moderation-dashboard: (1) a live inbound webhook
API so real content can be streamed through the pipeline in real time, making the
StreamMonitor animate with genuine events rather than replayed CSV rows; (2) a fine-tuned
Detoxify model (multi-label BERT classifier on Jigsaw) to fill the fourth model slot
and complete the zero-shot vs fine-tuned comparison narrative.

## Language(s)

Python (webhook endpoint, training script), TypeScript (no frontend changes required for webhook v1)

---

## Workstream A — Live Webhook API

### What it does
A `POST /ingest` endpoint on the existing FastAPI app (port 8002) that accepts
`{"text": "..."}`, publishes a `ModerationEvent` to the Kafka topic, and returns
`{"event_id": "<uuid>"}` in < 100ms. All existing consumers pick it up automatically.
The StreamMonitor event rate counter updates visibly within the next poll cycle (3s).

A companion `scripts/demo_stream.py` POSTs synthetic events at a configurable rate
so the dashboard can demo without any external client.

### Success Criteria
- `POST /ingest {"text": "some content"}` returns 200 + event_id in < 100ms
- Event is classified by all active consumers within ~5s of ingest
- StreamMonitor event rate increments on next poll
- CORS-enabled (same allowed origins as `/metrics/*`)
- `demo_stream.py --rate 5` runs cleanly and produces visible dashboard activity

### Constraints
- Must reuse the existing FastAPI app — no new service, no new port
- Webhook Kafka producer must be independent of the consumer-side producer (no shared instance)
- `correct` field: live webhook events have no ground truth — store `correct=None`; API and
  frontend must already handle nullable `correct` (confirm before implementing)
- Rate ceiling: 100 req/s is fine for demo; no auth required

### Out of Scope
- Authentication / API keys
- Batch ingest
- Frontend changes (StreamMonitor already polls)
- Persisting raw webhook payloads beyond Kafka

---

## Workstream B — Detoxify (fine-tuned) Model

### What it does
Fine-tune `bert-base-uncased` with a 6-label multi-label sigmoid head on Jigsaw, save
the checkpoint to `resources/models/toxicity-classifier-finetuned/detoxify-finetuned-best/`,
and wire it into the existing `finetuned_detoxify` consumer + seed-sim slot.

### The narrative unlock
The four-model lineup now tells two orthogonal stories:

| | Zero-shot | Fine-tuned |
|---|---|---|
| **Binary** | DistilBERT (F1 0.405) | DistilBERT (F1 0.882) |
| **Multi-label** | Detoxify (F1 0.904) | Detoxify fine-tuned (TBD) |

Detoxify zero-shot already leads at F1 0.904. The fine-tuned version trains on all 6
Jigsaw labels simultaneously — the hypothesis is that multi-label co-training improves
toxic recall while keeping precision high.

### Architecture
```
bert-base-uncased
  → Linear(768, 6)           # one logit per Jigsaw label
  → BCEWithLogitsLoss         # per-label binary cross-entropy
  → sigmoid + threshold 0.5  # multi-hot prediction per label
```
`correct` column uses binary toxic label (index 0) to stay consistent with other models.
`confidence` stores sigmoid(logit[0]) — the toxic probability.

### Training spec
| Param | Value |
|---|---|
| Base model | `bert-base-uncased` |
| Dataset | Jigsaw `train.csv` (159k rows, 80/20 split) |
| Labels | toxic, severe_toxic, obscene, threat, insult, identity_hate |
| Loss | `BCEWithLogitsLoss` |
| Epochs | 3 |
| Batch size | 32 (MPS-safe on M4 24GB) |
| LR | 2e-5, linear warmup ratio 0.1 |
| Device | MPS (`torch.device("mps")`) |
| Checkpoint | `resources/models/toxicity-classifier-finetuned/detoxify-finetuned-best/` |
| Eval JSON | `resources/evals/toxicity-classifier-finetuned/detoxify-finetuned-<timestamp>.json` |

Follow python-conventions.md HuggingFace Trainer section exactly:
- `torch.mps.synchronize()` in `on_save` callback (MPS checkpoint save bug)
- Save via `AutoModelForSequenceClassification` with `num_labels=6`

### Consumer + seed-sim integration
- `finetuned_detoxify` key already in `MODEL_REGISTRY` (added this session)
- `DETOXIFY_CHECKPOINT_PATH` env var already declared in `Settings`
- Consumer loads checkpoint with `AutoModelForSequenceClassification.from_pretrained(checkpoint, num_labels=6)`
- Inference: `sigmoid(logit[0]) >= 0.5` → predicted_label; `confidence = sigmoid(logit[0])`
- seed-sim already handles `finetuned_detoxify` via the generic fine-tuned branch in `seed_model()`

### Success Criteria
- 3 epochs complete without OOM on M4 MPS
- Eval JSON written: F1, precision, recall on Jigsaw test set (binary toxic label)
- `finetuned_detoxify` card on Model Performance tab shows active + F1 >= 0.85
- `seed-sim --models finetuned_detoxify --confirm` runs in < 5 min

### Out of Scope
- Multi-label scores surfaced in the frontend (v1: binary toxic label only)
- Fine-tuning RoBERTa (removed from model lineup)
- Hyperparameter search

---

## Open Questions for Planner

1. **Nullable `correct`**: does the `classifications` ORM model already have `correct`
   as `Boolean` (nullable)? Check `api/models.py`. If `NOT NULL`, a migration is needed
   before the webhook can write rows.
2. **Multi-label confidence storage**: for the finetuned_detoxify consumer, store only
   `confidence = sigmoid(logit[0])` in the existing float column — or add a JSON sidecar
   column for all 6 label scores? Recommend float only for v1 (no schema change needed).

---

## Handoff

**Next role:** planner

Planner should:
1. Scope Workstream A (webhook) as a single-session implementer task — 2–3 new files
   within the existing FastAPI app + one script
2. Scope Workstream B (Detoxify fine-tuning) as a model-trainer sequence running in
   `projects/toxicity-classifier-finetuned/` alongside project 8 scripts
3. Resolve the two open questions above before issuing implementer instructions
4. Confirm seed-sim `finetuned_detoxify` branch handles `num_labels=6` correctly
   (the generic branch calls `pipeline("text-classification", ...)` which expects a
   single-label head — multi-label inference needs a direct model call instead)
