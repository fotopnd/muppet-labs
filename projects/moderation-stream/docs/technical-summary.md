# moderation-stream — Technical Summary

**Status:** Complete (Phase 1 active, Phase 2 pending checkpoints)
**Date:** 2026-06-02

## What Was Built

moderation-stream is a Kafka-based content moderation pipeline that runs five machine learning classifiers in parallel against the same stream of text content, accumulates per-message predictions against labeled ground truth in Postgres, and surfaces live per-model accuracy, latency, and throughput in a React dashboard. The system is designed for direct model comparison under equivalent input conditions (all five classifiers receive every event from the same topic, in the same order, with no sampling or routing).

The dataset is the Jigsaw Toxic Comment Classification corpus (a publicly available collection of Wikipedia comments labeled for toxicity), replayed at configurable rate by a Python producer. Three Phase 1 classifiers are active: a DistilBERT (a lightweight transformer model) zero-shot classifier, a RoBERTa zero-shot classifier, and a Detoxify rule-based model. Two Phase 2 fine-tuned variants of the same architectures are registered and visible in the dashboard, though they wait for checkpoint delivery from a companion fine-tuning project before consuming. The pipeline is covered by infrastructure-free unit tests for the producer and consumer logic, and by integration tests for the metrics API that assert computed accuracy and latency values against seeded rows.

## Key Technical Decisions

- **Sync consumers, async metrics API:** Kafka consumers run blocking poll loops in their own processes, while the FastAPI metrics API is fully async, and the two share a Postgres database through separate SQLAlchemy engines with no cross-contamination of connection state. This keeps consumer timing deterministic and the API's concurrency model clean.

- **Phase-gated deployment via `MODEL_REGISTRY`:** A central registry object drives both the API's status logic and the frontend's rendering. Phase 2 models return a `pending_weights` status until a checkpoint path is configured, meaning the production system can activate fine-tuned models through a configuration change rather than a code deployment.

- **Server-side aggregation with `percentile_cont`:** Per-model accuracy, p50 and p95 latency percentiles, and 60-second rolling throughput are computed in a single `GROUP BY model_name` SQL query using PostgreSQL's ordered-set aggregate function. No computation happens on the API server or the client, and results are consistent regardless of when the dashboard polls.

- **Port isolation (5433 vs 5432):** Postgres runs on port 5433, reserving 5432 for the case-queue project that shares the same Docker environment. This was decided at architecture time and applied consistently across compose configuration, environment files, and test fixtures, avoiding any collision without environment-specific overrides.

- **Dashboard as route extension, not a new application:** The live metrics view is a `/stream` route added to the existing case-queue React application, sharing its component library, router, and query client. This kept deployment surface minimal and required no changes to the existing application's structure.

## Architecture Overview

A Python producer reads rows from the Jigsaw CSV at a configurable rate (default 10 messages per second) and publishes serialised event objects to a Kafka topic. Three to five consumer workers subscribe to that topic, each in its own Kafka consumer group to receive all messages independently, run inference on each text payload, write a classification result row (predicted label, latency in milliseconds, and correctness relative to the Jigsaw ground truth label) to Postgres, and commit the offset only after a successful write. The FastAPI metrics service queries that table on demand, returning aggregated statistics for all five models in a single response. The React dashboard polls the metrics endpoint every three seconds and renders one card per model, with active models showing live metrics and pending models showing a distinct waiting state.

## Known Gaps and Limitations

Phase 2 consumers exit without consuming when no checkpoint is present, which is correct behaviour, though it means two of the five model slots show zeros until that project delivers. Schema management uses SQLAlchemy `create_all` rather than Alembic-managed migrations, appropriate for a prototype and straightforward to replace. There is no consumer supervisor process, meaning a consumer crash requires a manual restart. The throughput metric is a 60-second rolling window count divided by 60, which lags actual throughput changes and understates burst rates.

## What's Next

Integrate Phase 2 fine-tuned model checkpoints once the companion project delivers them. Add all consumers as named services in the Docker Compose file so the full stack starts with a single command. Replace `create_all` with Alembic migrations for production schema management. Add a per-consumer health endpoint and a process supervisor for automatic restart on failure.
