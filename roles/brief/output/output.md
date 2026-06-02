# Brief Output — moderation-stream

**Role:** brief
**Sequence:** `new-project-full` (step 1)
**Date:** 2026-06-02

---

## Project Name

`moderation-stream`

---

## Description

A Kafka-based content moderation event streaming platform with a live five-model comparison pipeline. A Python producer replays the Jigsaw Toxic Comment dataset as a configurable-speed Kafka stream. Five classifier inference services run as independent Kafka consumers, each classifying every event in parallel. Per-model metrics are computed in real time against Jigsaw ground-truth labels: accuracy, p50/p95 decision latency, and throughput (cases/second). A new React dashboard route — added to the existing case-queue frontend — shows the five-way comparison live as the stream runs.

This is a phased project: Phase 1 launches with three zero-shot control models (no fine-tuning required, demo is immediately live). Phase 2 loads fine-tuned weights from project 8 to complete the comparison panel.

---

## Language(s)

- **Backend / streaming:** Python (Kafka producer, classifier consumers, metrics aggregation)
- **Frontend:** TypeScript (React route added to case-queue frontend)
- **Infrastructure:** Kafka via Docker Compose, FastAPI for metrics API
- **Tooling:** uv (Python), pnpm (TypeScript), Docker Compose

---

## Success Criteria

The project is done when all of the following are true:

1. **Kafka producer** — replays Jigsaw dataset as a stream at configurable speed (messages/second); each message contains the text and ground-truth label.
2. **Three Phase 1 classifier consumers** — DistilBERT zero-shot, RoBERTa zero-shot, Detoxify — each running as an independent Kafka consumer group, classifying every message, recording decision + latency.
3. **Metrics aggregation service** — collects per-model accuracy (vs ground truth), p50/p95 latency, and throughput; exposes them via a REST endpoint.
4. **React dashboard route** — new `/stream` route in the case-queue frontend showing the live five-way comparison panel; auto-refreshes every few seconds while the stream is running.
5. **Phase 2 slot** — loading fine-tuned DistilBERT and RoBERTa weights (from project 8) is a config change only; the platform handles five models from day one, with slots 4 and 5 showing "pending fine-tuned weights" until project 8 completes.
6. **Runs locally end-to-end** — `docker compose up` starts Kafka + Zookeeper; producer and consumers start with single commands; dashboard updates live.
7. **README** — explains the architecture, how to run Phase 1, and how to slot in project 8 weights for Phase 2.

---

## Five Models

| Slot | Model | Type | Phase |
|------|-------|------|-------|
| 1 | DistilBERT (`distilbert-base-uncased-finetuned-sst-2-english` or HuggingFace zero-shot pipeline) | Zero-shot control | Phase 1 |
| 2 | RoBERTa (`roberta-large-mnli` zero-shot classification) | Zero-shot control | Phase 1 |
| 3 | Detoxify (`unitary/toxic-bert` via `detoxify` library) | Pre-trained control | Phase 1 |
| 4 | Fine-tuned DistilBERT | Trained — weights from project 8 | Phase 2 |
| 5 | Fine-tuned RoBERTa | Trained — weights from project 8 | Phase 2 |

---

## Constraints

- **Portfolio-first:** architecture must be explainable and clean; not a monolith, not a mess of scripts.
- **CPU inference only:** all five transformer models run on CPU. No GPU dependency, no CUDA. Inference at 5–100ms per classification is acceptable.
- **No LLM API calls in the hot path:** all classification is local. Zero per-classification inference cost.
- **Freely available dataset:** Jigsaw Toxic Comment Classification Challenge (Kaggle, free download). Ground-truth labels enable real accuracy measurement.
- **Extends case-queue frontend:** the `/stream` dashboard route lives in `projects/case-queue/web/` — it is not a separate frontend project.
- **Phase 1 must be demo-ready without project 8:** Phase 2 slots are non-blocking placeholders at launch.
- **Hostinger KVM2 target (8GB RAM):** all five models + Kafka + Postgres + API + nginx must fit within 8GB for production deployment.

---

## Out of Scope

- Fine-tuning (project 8 is a separate project; project 22 only loads its output)
- Real-time ingestion from external APIs (replay of static Jigsaw dataset only)
- User authentication on the dashboard (header-based actor from case-queue is sufficient)
- Persistent stream storage / replay history (metrics are in-memory or short-lived Postgres; no long-term event store)
- Model serving infrastructure (TorchServe, Triton, etc.) — direct Python inference is sufficient
- Multi-topic or multi-dataset streaming (Jigsaw only for Phase 1)

---

## Assumptions

1. **Kafka via Docker Compose** — Confluent `cp-kafka` or Bitnami image; single broker + Zookeeper is sufficient for local and VPS deployment.
2. **`confluent-kafka-python`** — preferred Kafka client for Python (lower latency than `kafka-python`; well-maintained).
3. **HuggingFace `transformers` + `pipeline`** — standard interface for all transformer inference; Detoxify wraps this under the hood.
4. **Metrics aggregation runs as a FastAPI service** — separate process from consumers; persists per-model rolling metrics to Postgres or a shared in-memory store, exposed as a REST endpoint that the frontend polls.
5. **Case-queue frontend extended, not replaced** — `/stream` is a new React route; existing case-queue routes (`/`, `/cases/:id`, `/audit`) are untouched.
6. **Jigsaw dataset assumed to be downloaded locally** before running the producer — no automated download in the producer; README documents the Kaggle download step.
7. **Project lives at** `projects/moderation-stream/` — producer, consumers, metrics API, and shared types all live here. Frontend additions land in `projects/case-queue/web/`.
8. **Phase 2 model loading** is controlled by env vars pointing to checkpoint paths — if the env var is unset, the slot shows "pending" in the dashboard.

---

## Handoff

**Next role:** planner
**What the planner does with this:**
- Confirm or revise the Kafka setup (broker image, topic design, consumer group strategy).
- Define the full module structure: producer, consumers (one per model), metrics service, shared types.
- Define the REST API contract for the metrics endpoint — what the frontend polls.
- Define the React component structure for the `/stream` dashboard route.
- Identify open questions with proposed answers (per routing.md convention).
- Confirm whether metrics are persisted to Postgres or held in-memory (trade-off: simplicity vs restartability).

**Flags for planner:**
- Assumption 4 (metrics store) — in-memory dict vs Postgres vs Redis; planner should decide and document.
- Assumption 2 (Kafka client) — confirm `confluent-kafka-python` vs `kafka-python`; both work, different install friction on M1/M2.
- Phase 2 slot design — planner should specify exactly how a Phase 2 model is enabled (env var, config file, CLI flag).
