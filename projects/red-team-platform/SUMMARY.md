# Red-Team Platform — Executive Summary

## The Problem

Running jailbreak attacks against a language model is straightforward. Understanding what the results mean is not. A simple pass/fail record tells you whether attacks succeeded, though it does not tell you which attack mechanisms are most dangerous, whether those results connect to the broader monitoring infrastructure, or what the failure looks like when a successful attack reaches a deployed system. Without instrumentation, red-teaming produces a number rather than actionable safety intelligence.

## What Was Built

A platform that runs structured attack campaigns against a language model, scores every response with a safety classifier, clusters successful attacks by mechanism, and publishes every result directly into the live safety monitoring pipeline. The platform is corpus-driven: attacks are drawn from a published jailbreak dataset, making campaigns reproducible. Results are stored with full provenance (strategy, harm category, classifier score, cluster assignment) and accessible through a React dashboard.

## Why It Matters

The platform demonstrates the instrumentation layer that makes red-teaming useful rather than just executable. Every attack result is a classified, clustered event in the monitoring system, not a row in a spreadsheet. This maps directly to the Anthropic Safeguards signal: detecting and measuring unwanted model behaviors in a way that connects to the broader safety infrastructure.

The integration with the safety monitor is concrete: successful attack events are published via an outbox publisher to the monitor's Kafka topic, where they are consumed by the same classifiers that process live traffic. An engineer reviewing the monitor's dashboard after a red-team run sees real bypass events, not synthetic test fixtures.

## What Was Demonstrated

Phase 1 sweep: 1,797 attacks across 6 strategies against gemma2:9b, running on a RunPod RTX 4090 at $1.08 total cost. Results revealed a clean two-cluster pattern with no middle ground:

| Strategy | ASR | Mechanism |
|----------|-----|-----------|
| few_shot_json | 1.000 | Output-format bypass |
| evil_system_prompt | 0.997 | Persona bypass |
| gcg | 0.997 | Adversarial suffix |
| AIM | 0.000 | Resisted (fast refusal) |
| combination_1 | 0.000 | Resisted |
| refusal_suppression | 0.000 | Resisted (fastest refusal) |

The latency signature distinguishes the clusters: blocked strategies trigger short, fast refusals (avg 2.0–3.3s), while bypass strategies produce long, on-topic responses (avg 2.9–9.7s). The few_shot_json strategy achieved 100% bypass by wrapping requests in a JSON output format, suppressing safety-relevant filtering entirely.

8 semantic clusters across 896 successful attacks, covering harm categories including synthetic drug synthesis, assassination planning, and manipulation content. All 1,797 events published to the safety monitor via the outbox publisher.

## What Extension Would Require

- Additional models (the runner supports any Ollama-compatible model with a config change)
- Multi-turn attack strategies (current design assumes single-turn)
- Automated regression testing: the benchmark infrastructure supports scheduled re-runs to detect changes in model behaviour across deployments
- Live production integration: the outbox publisher schema is compatible with any Kafka consumer that accepts the LLMInteractionEvent format

## Appendix: Technical Details

The platform uses FastAPI, PostgreSQL, Kafka (Confluent), and scikit-learn for TF-IDF clustering. The attack runner integrates the shared `llm-safety-classifier` package to score responses inline. The outbox publisher uses `FOR UPDATE SKIP LOCKED` to ensure concurrent publisher instances do not duplicate events. Full architecture and implementation decisions are in the [Technical Deep-Dive](README.md).
