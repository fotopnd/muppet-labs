# project_learnings.md — moderation-dashboard

> Running log of design decisions, adversarial critiques, pivot points, and lessons learned.
> Append new entries at the top. Each entry is dated and titled.

---

## 2026-06-06 — Adversarial portfolio review: strong infrastructure, weak analysis

### The honest assessment

The project is technically competent but does not yet demonstrate Safeguards understanding. It demonstrates Kafka, FastAPI, React, PostgreSQL, multi-model inference pipelines, and async consumer patterns. Those are strong DE/SWE signals for a generalist role. They are not Safeguards signals.

The difference between "good ML engineering portfolio" and "Safeguards portfolio" is whether the project shows you understand *why* safety classifiers fail and *how* you would detect and respond to that failure in production. This project shows the plumbing. It does not show understanding of the water.

### What the project actually does

Three toxicity classifiers (DistilBERT zero-shot, Detoxify, DistilBERT fine-tuned) consume a live Bluesky firehose via Kafka. Every post is classified by all three in parallel via a shadow consumer group. A FastAPI backend stores results in Postgres and exposes metrics. A React dashboard shows per-model F1/latency/throughput, a live flag rate, a category breakdown, a disagreement panel, time-series charts, anomaly detection via z-score, and a human review queue that escalates low-confidence or disagreement cases to a case-queue service.

### Adversarial findings

**F1: The task is not Anthropic's problem.**
Anthropic Safeguards classifies Claude's outputs and users' inputs for policy violations — jailbreaks, harmful requests, CSAM, deception. Classifying third-party Bluesky posts for toxicity is a generic NLP exercise. Nothing in this project required understanding why safety classifiers fail on adversarial inputs, how policy definitions translate to label schemas, or how human reviewers develop calibration over time.

**F2: The 38.6% flag rate is described, not understood.**
The live flag rate gap (38.6% vs 11–13%) is displayed as a number. The project has no hypothesis about why the gap exists, no analysis of what the zero-shot model is flagging that fine-tuned rejects, no calibration curve, no false-positive estimate. "Here is a surprising number" is not a safety insight. A Safeguards engineer would immediately ask: is DistilBERT over-flagging borderline political content? Sarcasm? Non-English text? The raw posts are in the DB. The question is not being asked.

**F3: The disagreement panel shows samples but derives no conclusion.**
274 disagreements/hour, top category "clean" — displayed, not analyzed. The panel shows 10 random posts with split verdicts. It does not ask: are these posts systematically adversarial? Do they share patterns? Is the disagreement clustered by confidence level? Is there a threshold where ensemble agreement would reduce human review volume by X%? Showing samples is a feature. Deriving insight is what Safeguards work actually is.

**F4: F1 against Jigsaw labels on Bluesky is not a valid evaluation.**
The seeded F1 numbers (0.847 for DistilBERT, 0.882 for fine-tuned) are computed against Jigsaw ground truth on Jigsaw-distributed data. There is no ground truth for live Bluesky posts. So "live flag rate" is not "live false positive rate" — there is no way to know how many of the 38.6% flagged posts are genuinely toxic vs false positives using current tooling.

**F5: The human review queue is a dead end.**
Cases are escalated. Reviewers can approve or reject. That decision goes nowhere — no feedback to classifier thresholds, no re-ranking of escalation priority, no label generation for retraining. In a real Safeguards system the human review loop is the most valuable signal. Here it is a UI feature.

**F6: Infrastructure is strong, analysis is weak.**
The technical choices (Kafka, shadow routing, async consumers, Alembic, anomaly detection z-score, TanStack Query) are all defensible and solid. The problem is that the system collects all the right data and then asks the wrong questions about it.

### What genuinely maps to Safeguards (buried signals)

**Signal 1: Distribution shift measurement.**
A model trained on Jigsaw and deployed on live Bluesky produces a 3× higher flag rate than a fine-tuned model. This IS distribution shift — the exact problem Safeguards teams face when deploying safety classifiers against real traffic. The data exists to show this rigorously.

**Signal 2: Confidence-based escalation as a calibration proxy.**
The escalation service triggers on confidence < 0.6. The rate at which each model triggers this threshold, disaggregated by content category, is an implicit calibration measurement. This data is in the DB. It is not surfaced.

**Signal 3: Model disagreement as an adversarial signal.**
When three classifiers trained on the same task give different verdicts on the same post, that post is either adversarially constructed, ambiguously worded, or at a category boundary — precisely where Safeguards classifiers are weakest. The project captures disagreement counts. It does not characterize the disagreement.

### What would transform this into a Safeguards portfolio piece

Three additions in order of impact:

1. **Calibration Analysis tab.** Reliability diagram per model on seeded data (confidence decile → accuracy). Confidence distribution comparison between seeded and live data — the divergence IS the distribution shift finding. Mean confidence for agreed vs disagreed predictions on live data. This concretely shows whether confidence scores are meaningful — the most fundamental question in production safety classifier deployment.

2. **Distribution shift framing.** Replace the raw "Live flag rate: 38.6%" stat with a framed finding: *"DistilBERT zero-shot flags 3.4× more live posts than the fine-tuned model. This divergence is absent on the Jigsaw test set (F1 gap: 0.847 vs 0.882), suggesting calibration drift from domain mismatch — the zero-shot decision boundary was learned from annotation norms, not Bluesky content patterns."* That is a safety insight, not a metric.

3. **Disagreement characterization by confidence band.** Replace random samples with: disagreement rate by confidence band (both models low confidence vs one high/one low vs both high), and a majority-vote agreement rate as a live calibration proxy. This turns "here are some examples" into "here is what causes classifier disagreement."

### The question that must be answered before portfolio submission

*"What did you learn about classifier behavior from this system that you could not have learned from an offline benchmark?"*

Currently the honest answer is: "The flag rates differ." That is not enough.

After the calibration analysis additions, the answer should be: "I built a system that reveals how toxicity classifiers degrade when deployed outside their training distribution, measured the confidence-accuracy relationship under domain shift, and quantified which types of content drive systematic model disagreement. The key finding was X." That is a Safeguards story.

---

## 2026-06-05 — Safety-signal additions shipped

**What was added:**
- Live flag rate per model card (38.6% / 13.2% / 11.3%) — visible side-by-side without clicking
- `GET /metrics/disagreements` endpoint — total last hour, breakdown by category, 10 sampled posts with per-model verdicts
- `DisagreementPanel` component in ModelComparison tab
- `_LIVE_COUNTS_SQL` — shadow group, seeded=false, separate from existing `_METRICS_SQL`

**Lesson:** Adding the signal is not the same as analyzing it. The flag rate gap was always in the DB. Surfacing it was a good first step. Explaining it is the next required step.

---

## 2026-06-04 — Live Bluesky streaming verified

**What changed:**
- Replaced synthetic demo stream with live Bluesky firehose (`scripts/bsky_stream.py`)
- bsky-stream → POST /ingest → Kafka → 3 consumers → classifications table at ~4.5 events/sec
- finetuned_detoxify training killed, dropped from registry — 3 active models now
- Category inference fixed: unknown → toxic/clean based on predicted_label

**Lesson:** Real data immediately surfaced the flag rate gap (38.6% vs 11%). Synthetic data had masked this. Using live data early is almost always the right call for a portfolio project — the unexpected findings are the story.

---

## 2026-06-03 — moderation-dashboard defined as unified successor

**Decision:** Unified content moderation platform (project 28) supersedes moderation-stream (project 22). One deployed site tells the full story: production round-robin routing + shadow parallel evaluation + dbt analytics layer + escalation.

**Lesson:** The project architecture (shadow vs production consumer groups, Kafka round-robin) is genuinely interesting engineering. The risk is that it becomes an infrastructure showcase without a safety-analysis payoff. This risk materialized — addressed in 2026-06-06 entry above.
