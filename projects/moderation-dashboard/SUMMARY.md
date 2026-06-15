# Moderation Dashboard — Executive Summary

## The Problem

A model that performs well in offline evaluation often fails in ways that are invisible without production infrastructure around it. F1 scores on held-out test sets measure what a model knows; they don't measure what happens when traffic is split across models, when confidence is unexpectedly low, or when two models that should agree on a label don't. Real ML platforms require routing, shadow evaluation, anomaly detection, and escalation — the operational layer that turns a model into a system.

## What Was Built

A streaming content moderation platform that ingests 159,000 Jigsaw toxic comment events via Kafka and routes them through two independent consumer groups simultaneously: a **production group** that distributes traffic round-robin across DistilBERT and Detoxify (simulating real traffic splitting), and a **shadow group** where all models evaluate every event in parallel (enabling apples-to-apples comparison without affecting production routing). An anomaly detector runs a rolling z-score over 5-minute windows and flags deviations in flag rate. An escalation service routes low-confidence events and shadow disagreements to a human review queue. A dbt transform layer materialises classification results into analytics aggregates. A React dashboard surfaces all five layers: live stream throughput, per-model performance, shadow comparison, human review queue, and category trend analytics.

## Why It Matters

Production ML monitoring at Anthropic's scale requires exactly this infrastructure: the ability to run a challenger model in shadow alongside a production model, detect when they disagree, escalate uncertainty rather than swallowing it, and surface anomalies in the event stream before they become incidents. This project makes each of those operational layers concrete and independently testable.

## What Was Demonstrated

The fine-tuned DistilBERT classifier was evaluated on the Jigsaw held-out test set (n=15,958):

| Model | F1 | Precision | Recall | AUC-ROC |
|---|---|---|---|---|
| DistilBERT zero-shot | 0.322 | 0.206 | 0.745 | 0.720 |
| DistilBERT fine-tuned (Jigsaw) | 0.847 | 0.828 | 0.867 | 0.924 |
| Delta | **+0.525** | **+0.622** | **+0.122** | **+0.204** |

The fine-tuned model is active in the shadow group only — allowing live comparison against zero-shot performance without changing production routing. Shadow disagreement between the two DistilBERT variants (same architecture, different weights) is a clean signal: when they disagree, one of them is wrong, and that event is worth human review.

Per-category accuracy on the fine-tuned model: severe_toxic 0.909, obscene 0.949, threat 0.902, insult 0.946, identity_hate 0.908.

## Known Limitations

**Escalation is threshold-based.** The confidence threshold of 0.6 for escalation was chosen without calibration against a target false-positive rate. In a production system, this threshold should be derived from the operating point on a precision-recall curve against a labelled validation set.

**Anomaly detector resets on restart.** The rolling z-score builds its baseline from the current session. A newly restarted service will flag the first few minutes of normal traffic as anomalous until the baseline window fills. This is a deliberate design trade-off (no stale baselines) but requires warm-up awareness in deployment.

**No ground truth for live events.** The Jigsaw corpus provides labels for seeded evaluation, but events published to the live stream have no ground-truth labels at classification time. F1 metrics in the dashboard reflect seeded data only; live throughput and escalation rate are the observable production signals.

**Single topic, single partition.** The current Kafka configuration uses one topic and one partition, which limits throughput to approximately 10 events/sec. Horizontal scaling would require partitioning by content category or producer shard.

## What Extension Would Require

- Ground-truth feedback loop: human review decisions fed back to a labels table, enabling online evaluation of live events
- Multi-model production routing: a third model added to the production group (requires consumer group rebalancing)
- Persistent anomaly baseline: the rolling window state serialised to PostgreSQL so the detector survives restarts without a cold-start period
- Deployment: the full stack (Kafka, PostgreSQL, FastAPI, React) runs on Docker Compose and targets Hetzner CX33

## Appendix: Technical Details

**Backend:** Python · FastAPI · Kafka (confluent-kafka) · PostgreSQL · SQLAlchemy async · dbt · asyncpg  
**ML:** HuggingFace Transformers · Detoxify · DistilBERT  
**Frontend:** React 19 · TypeScript · Tailwind v4 · Recharts · TanStack Query  
**Infra:** Docker Compose (Kafka + Zookeeper + Postgres on port 5434)

Architecture, key design decisions, and full running instructions are in [README.md](README.md).
