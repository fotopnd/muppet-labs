# Implementer Output — moderation-dashboard v2 additions

**Role:** implementer
**Sequence:** v2-planner → implementer
**Date:** 2026-06-05

---

## Files Produced

### Workstream A — Webhook /ingest

| File | Purpose |
|------|---------|
| `alembic/versions/20260605_c4d5e6f7a8b9_nullable_correct.py` | Migration: make `classifications.correct` nullable |
| `moderation_dashboard/api/routers/ingest.py` | `POST /ingest` handler — publishes `ModerationEvent` to Kafka |
| `scripts/demo_stream.py` | CLI: POST Jigsaw-sampled events at configurable rate |

### Workstream A — Modified Files

| File | Change |
|------|--------|
| `moderation_dashboard/types.py` | `ground_truth: int \| None`, `category` default `"unknown"` |
| `moderation_dashboard/api/models.py` | `correct: Mapped[bool \| None]`, `nullable=True` |
| `moderation_dashboard/api/schemas.py` | Added `IngestRequest`, `IngestResponse` |
| `moderation_dashboard/api/main.py` | Registered `ingest_router` |
| `moderation_dashboard/consumers/base.py` | `correct = None` when `ground_truth is None` |
| `moderation_dashboard/api/routers/ingest.py` | New |
| `pyproject.toml` | Added `demo-stream` entry point |
| `.env.example` | Updated checkpoint var names (roberta → detoxify) |

### Workstream B — Detoxify fine-tuned

| File | Purpose |
|------|---------|
| `projects/toxicity-classifier-finetuned/toxicity_classifier/train_detoxify.py` | bert-base-uncased 6-label training script |
| `projects/toxicity-classifier-finetuned/toxicity_classifier/evaluate_detoxify.py` | Eval on Jigsaw test split, binary toxic F1 |

### Workstream B — Modified Files

| File | Change |
|------|--------|
| `projects/toxicity-classifier-finetuned/toxicity_classifier/cli.py` | Added `detoxify` model option to train + eval commands |
| `moderation_dashboard/consumers/finetuned.py` | Added `FinetunedDetoxifyConsumer` (direct 6-label sigmoid inference) |
| `moderation_dashboard/consumers/runner.py` | Replaced `finetuned_roberta` branch with `finetuned_detoxify` |
| `moderation_dashboard/seed_sim.py` | Added `finetuned_detoxify` branch (direct model inference, not pipeline) |

---

## Setup Steps Taken

- `uv run alembic upgrade head` — applied nullable_correct migration
- Restarted API and consumers to pick up `types.py` change

---

## Deviations from Plan

- `roberta` branch removed from `runner.py` (model no longer in registry) — existing `roberta` key in runner was dead code since `MODEL_REGISTRY` no longer has it. Runner uses `choices=list(MODEL_REGISTRY.keys())` so argparse blocks it anyway.
- `demo_stream.py` entry point is `scripts.demo_stream:main` — requires `scripts/` to be importable. Works when run from the project root via `uv run demo-stream`.

---

## Known Gaps

- **Training not yet run**: `finetuned_detoxify` consumer and seed-sim branch are implemented and tested for structure, but the checkpoint doesn't exist yet. Card shows `pending_weights` on the dashboard. Run training to complete:
  ```
  cd projects/toxicity-classifier-finetuned
  caffeinate -i uv run train --model detoxify --output-dir checkpoints --epochs 3 --batch-size 32
  ```
  Then set `DETOXIFY_CHECKPOINT_PATH` in `projects/moderation-dashboard/.env` and run:
  ```
  uv run seed-sim --confirm --models finetuned_detoxify
  ```
- **`scripts/` package**: `demo_stream.py` imports `moderation_dashboard.config`. Needs an `__init__.py` in `scripts/` to be importable as a package, or the entry point can be changed to use `importlib`. Currently relies on `uv run` from project root resolving the module path.

---

## How to Run

### Webhook
```bash
# API must be running
uv run md-api

# Test the endpoint
curl -X POST http://localhost:8002/ingest \
  -H "Content-Type: application/json" \
  -d '{"text": "Some content to moderate"}'
# → {"event_id": "<uuid>"}

# Run synthetic stream (3 events/sec)
uv run demo-stream
uv run demo-stream --rate 10 --api http://localhost:8002
```

### Detoxify training (Workstream B, not yet run)
```bash
cd projects/toxicity-classifier-finetuned
caffeinate -i uv run train --model detoxify --output-dir checkpoints --epochs 3 --batch-size 32
uv run evaluate --model detoxify \
  --checkpoint-dir checkpoints/detoxify-finetuned-best \
  --output-dir /path/to/resources/evals/toxicity-classifier-finetuned/
```

---

## Handoff

Next role: reviewer

Key things for reviewer to check:
1. `ingest.py` — thread safety of module-level `Producer` singleton under async FastAPI
2. `base.py` — confirm `correct = None` handled correctly in SQL (NULL in SUM CASE WHEN)
3. `finetuned.py` — `FinetunedDetoxifyConsumer.classify()` tensor indexing `logits[0, 0]`
4. `seed_sim.py` — `finetuned_detoxify` branch: `_det_model` closure variable capture
5. `scripts/` importability — confirm `demo-stream` entry point resolves correctly
6. `train_detoxify.py` — `problem_type="multi_label_classification"` compatibility with installed transformers version
