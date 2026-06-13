# Moderation Dashboard — Project Summary

## What it is

A real-time content moderation platform that runs multiple ML classifiers in parallel via Kafka, compares them using a shadow evaluation architecture, detects anomalies in the event stream, and escalates low-confidence cases for human review. The system demonstrates how a production ML platform actually operates: not just a model, but the full feedback loop of routing, evaluation, monitoring, and escalation.

## Why it was built

Production ML systems don't run one model in isolation — they route live traffic, compare candidates in shadow, detect drift, and escalate uncertainty. This project makes that infrastructure concrete and observable. It's built as a portfolio piece for safety-adjacent ML engineering roles where understanding the operational layer around models matters as much as training them.

## Architecture

```
Jigsaw toxic comments (159k rows)
  → Kafka producer (rate-controlled, 10 events/sec)
  → Two consumer groups in parallel:

    Production group (round-robin routing)
      DistilBERT zero-shot ──┐
      Detoxify               ├── each model sees ~50% of events
                             └── simulates real production routing

    Shadow group (all-model evaluation)
      DistilBERT zero-shot ──┐
      Detoxify               ├── all models see every event
      DistilBERT fine-tuned  ┘   enables apples-to-apples comparison

  → Anomaly detector (rolling z-score on 5-min windows)
  → Escalation service (low confidence OR shadow disagreement → case queue)
  → dbt transforms (classification → analytics aggregates)
  → FastAPI (port 8002) → React dashboard (5 views)
```

## Models

| Model | Type | Group | Status |
|-------|------|-------|--------|
| DistilBERT zero-shot | Binary toxicity classifier, no fine-tuning | Production + Shadow | Active |
| Detoxify | Multi-label toxicity (6 categories), pre-trained | Production + Shadow | Active |
| DistilBERT fine-tuned | Jigsaw fine-tuned (F1=0.85 on held-out test) | Shadow only | Pending weights |

## Key design decisions

**Round-robin vs shadow evaluation are separate questions.** Round-robin routing answers "which model handles production load?" — each model sees different events, simulating real traffic splitting. Shadow evaluation answers "how do models compare on the same input?" — all models see every event. Both consumer groups run simultaneously.

**Anomaly detection is stateless across restarts by design.** The rolling window z-score detector (`RollingWindowDetector`) builds its baseline from the current session's history. This means it adapts to the current traffic distribution rather than being anchored to stale baselines from a previous run.

**Escalation triggers are composable.** Two independent signals escalate to the case queue: `confidence < 0.6` (model uncertainty) and shadow disagreement (models disagree on label). Either alone escalates; both together flag the same event once. The escalation service polls on a configurable interval rather than consuming from Kafka directly.

**Seeded data separates evaluation from live inference.** A pre-generated seeded dataset with known ground-truth labels lets the Model Performance view show F1/precision/recall before any live data has accumulated. Live events (no ground truth) contribute to throughput and volume metrics but not accuracy.

## Dashboard views

| View | What it shows |
|------|---------------|
| **Stream Monitor** | Live event rate, category distribution (stacked area chart by minute), anomaly feed |
| **Model Performance** | Per-model F1 / precision / recall / latency p50/p95 / throughput, with rolling sparklines |
| **Model Comparison** | Shadow-group side-by-side verdicts for a single event — confidence and correctness across all models |
| **Human Review** | Escalation queue: events routed for human decision (low confidence or model disagreement) |
| **Analytics** | Category trend heatmap (48h), hourly F1 trajectory per model, escalation rate over time |

## Stack

**Backend:** Python · FastAPI · Kafka (confluent-kafka) · PostgreSQL · SQLAlchemy async · dbt · asyncpg  
**ML:** HuggingFace Transformers · Detoxify · DistilBERT  
**Frontend:** React 19 · TypeScript · Tailwind v4 · Recharts · TanStack Query  
**Infra:** Docker Compose (Kafka + Zookeeper + Postgres on port 5434)

## Test coverage

- `tests/test_consumers.py` — classification label/latency (mocked classify)
- `tests/test_anomaly.py` — z-score computation, window boundary arithmetic
- `web/src/test/` — StreamMonitor, ModelPerformance, ModelComparison, HumanReview, Analytics (MSW mocks)

## Running locally

```bash
docker compose up -d          # Kafka + Postgres
uv run alembic upgrade head   # schema
uv run make all               # producer + 2 consumers + API + anomaly detector
cd web && pnpm dev            # dashboard on :5174
```
