# LLM Safety Monitor — Executive Summary

## The Problem

A single classifier making binary safe/unsafe decisions about LLM interactions has a fundamental weakness: when it is wrong, nothing catches it. Safety classifiers are imperfect by definition, and a system that depends on one classifier's judgment has no mechanism to detect its own errors. Real-world safety monitoring requires more than a final verdict. It requires a mechanism to surface the interactions where the system's own confidence is misplaced and human review is warranted.

## What Was Built

A streaming pipeline that classifies every LLM interaction in real time using three independently fine-tuned transformer models: a response-level safety classifier, a prompt intent classifier, and a harm taxonomy classifier. An escalation router waits for all three classifiers to return results, compares them against a configurable priority matrix, and routes interactions to a case review queue when the classifiers disagree or when specific high-severity patterns are detected. A React dashboard shows live event throughput, classifier distributions, and flagged interactions awaiting review.

## Why It Matters

The key design insight is that inter-classifier disagreement is itself a safety signal. When two classifiers that look at an interaction from different angles reach different conclusions, that conflict is more informative than either verdict alone. The architecture treats disagreement as the primary routing signal, rather than relying on any single classifier's confidence score to reach a threshold.

This design maps to the Anthropic Safeguards Infrastructure role at multiple levels: it implements data storage infrastructure (PostgreSQL with a full record of each classification result), evaluation metrics (held-out accuracy scores for all three classifiers), review tooling (case queue integration and review dashboard), and real-time classification at scale.

## What Was Demonstrated

Three classifiers evaluated on held-out test sets from published safety datasets (HH-RLHF and WildGuard). F1 score is a standard accuracy measure that combines how often a flag is correct (precision) with how often a real issue is caught (recall):

| Classifier | Task | F1 | Eval samples |
|------------|------|-----|------|
| Pair | Response-level safety | 0.549 | 6,337 |
| Prompt | Intent detection | 0.818 | 2,512 |
| Taxonomy | Harm category (13 classes) | 0.787 macro | 4,337 |

The pair classifier's F1 of 0.549 reflects a deliberate design choice: it is tuned to catch as many harmful interactions as possible (recall 0.910), accepting more false flags in return. A safety-conservative classifier should flag more than it misses. The escalation router then uses all three classifiers together, so the pair classifier's high recall feeds disagreement detection rather than triggering direct escalation on its own.

These figures are measured on a held-out WildGuard test split, where harm labels are human-curated. The live production stream uses HH-RLHF data, where "chosen" responses are bulk-labelled safe regardless of topic — inflating apparent false-positive rates. The dashboard exposes a WildGuard-only filter for this reason.

25/25 integration tests pass. 1,797 red-team attack events were published into the monitor's Kafka topic from the red-team platform and processed through the full classification and escalation pipeline.

## What Extension Would Require

- Multi-turn context: the current pipeline classifies each interaction independently without conversation history
- Classifier retraining: model checkpoints are stored at `resources/models/`. The training pipeline supports custom datasets and evaluation on held-out splits.
- Production deployment: the full stack (Kafka, PostgreSQL, FastAPI, React) fits in 8GB RAM, and deployment scripts target Hetzner CX33
- Additional harm taxonomy categories: the taxonomy classifier currently covers 13 WildGuard categories. Extending to custom categories requires labelled training data and a retraining run.

## Appendix: Technical Details

The monitor uses Kafka (Confluent) as the event transport, RoBERTa-base as the base model for all three classifiers, FastAPI for the API layer, PostgreSQL for interaction and classification storage, and React/TypeScript for the dashboard. The escalation router is a pure function tested independently of the database. Full architecture and implementation decisions are in the [Technical Deep-Dive](README.md).
