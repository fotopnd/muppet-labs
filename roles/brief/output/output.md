# Brief Output — llm-safety-monitor

**Date:** 2026-06-06
**Sequence:** new-project-full (v3 of moderation-dashboard — substantial rework, existing Kafka/FastAPI/React infrastructure carries over)
**Role executing:** brief

---

## Project Name

llm-safety-monitor

## Description

A streaming LLM safety classification platform that runs a continuous stream of real LLM interactions through three purpose-trained safety classifiers — a pair safety classifier, a prompt adversarial detector, and a harm taxonomy classifier — and routes flagged interactions to a human review queue based on a 2×2 prompt/response verdict matrix rather than a confidence threshold.

## Language(s)

Python (training, consumers, FastAPI backend) + TypeScript (React dashboard)

## Context and Motivation

This is a ground-up rework of the moderation-dashboard project. The streaming infrastructure (Kafka, async consumers, shadow routing, FastAPI, Postgres, React dashboard, case-queue escalation) is retained. Everything else — training data, model task, event schema, classification logic, escalation logic, and dashboard framing — is replaced.

The prior version classified Bluesky social posts for toxicity using Jigsaw-trained models. The adversarial portfolio review on 2026-06-06 established that this task is not relevant to Anthropic Safeguards. The new version classifies LLM interactions (prompt + response pairs, and prompts alone) for safety policy violations using datasets produced specifically for LLM safety research.

The key deliverable is a working system that can answer: *"Given a stream of LLM interactions, which ones violated a safety policy, what kind of violation, and how confident are we?"* — and surface the cases where classifiers disagree or fail.

---

## Datasets

Four datasets, two classification targets.

### Pair classification (prompt + response)

**Anthropic HH-RLHF** (`Anthropic/hh-rlhf`, HuggingFace)
- ~170k human-Claude conversation pairs
- Label: `chosen` (harmless response) vs `rejected` (harmful response)
- Binary safe/unsafe at the response level
- Primary training data for the pair safety classifier
- Directly from Anthropic — provenance is portfolio-relevant

**WildGuard** (`allenai/wildguard`, HuggingFace)
- ~92k prompt + response pairs
- Label: 13 harm categories (hate, violence, sexual content, PII, copyright, etc.) + binary safe/unsafe per category
- Dual use: contributes to pair classifier training (binary label) and trains the harm taxonomy classifier (13-category label)
- Broadens coverage beyond HH-RLHF's harmlessness framing

### Prompt classification (prompt only)

**AdvBench** (`llm-attacks/AdvBench`, HuggingFace / CSV)
- ~520 adversarial harmful instructions
- Label: implicitly harmful (all positives — requires sampling negatives from HH-RLHF chosen prompts)
- Covers: bioweapons instructions, malware, radicalization, fraud, self-harm facilitation

**JailbreakBench** (`JailbreakBench/JailbreakBench-artifacts`, HuggingFace)
- ~100 harmful behaviors × multiple jailbreak prompt variants = ~1,000–3,000 prompt examples
- Label: adversarial prompt (all positives — same negative sampling approach as AdvBench)
- Covers jailbreak techniques: role-play bypasses, prompt injection, encoding tricks

**Prompt classifier training composition:**
- Positives: AdvBench + JailbreakBench prompts + WildGuard harmful prompts (subset, ~3,000 total)
- Negatives: HH-RLHF chosen-side conversation openers + WildGuard safe prompts (~3,000 sampled)
- Total: ~6,000 balanced examples. Small but focused — planner to assess whether augmentation is needed.

---

## The Three Models

**Model 1 — Pair safety classifier**
- Base: DistilBERT (proven on this task class, fast on MPS)
- Training data: HH-RLHF (primary) + WildGuard binary label (secondary)
- Input: prompt + `[SEP]` + response (concatenated, max 512 tokens)
- Output: binary (safe / unsafe response)
- Ground truth available for all training examples → calibration analysis is fully valid

**Model 2 — Prompt adversarial detector**
- Base: DistilBERT
- Training data: AdvBench + JailbreakBench + WildGuard harmful prompts (positives) vs HH-RLHF benign prompts (negatives)
- Input: prompt only
- Output: binary (benign / adversarial)
- This model operates on the prompt before any response is generated — mirrors a real-time input filter

**Model 3 — Harm taxonomy classifier**
- Base: DistilBERT with multi-label head (BCEWithLogitsLoss, same pattern as finetuned_detoxify attempt)
- Training data: WildGuard 13-category labels
- Input: prompt + `[SEP]` + response
- Output: 13 binary labels (one per harm category) — a single interaction can trigger multiple categories
- This model answers "what kind of harm" rather than "is there harm"

---

## Event Schema

Each stream event represents one LLM interaction:

```
{
  "event_id": "uuid",
  "prompt": "...",
  "response": "..." | null,        // null for prompt-only events from AdvBench
  "source_dataset": "hh-rlhf" | "wildguard" | "advbench" | "jailbreakbench" | "live",
  "ground_truth_safe": true | false | null,   // null for live Claude API events
  "ground_truth_categories": ["hate", ...] | null
}
```

Consumers produce classification rows per model per event, same schema as existing `classifications` table with `content` = prompt text (truncated), new `response_text` column, `predicted_label` = safe(0)/unsafe(1), `confidence` = float.

---

## Live Data Stream

**Primary: dataset replay** (zero API cost, zero account risk)
- A replay producer samples from all four datasets at configurable rates, shuffling source datasets
- Default mix: 60% HH-RLHF, 25% WildGuard, 10% AdvBench, 5% JailbreakBench
- Rate: ~1 event/3 seconds (manageable for a demo, produces ~1,200 events/hour)
- Ground truth labels are available → all evaluation metrics are meaningful in real time
- **Principled choice, not just a cost call**: the classifiers operate on real adversarial data (AdvBench harmful instructions, JailbreakBench jailbreak prompts). Claude never receives this content. The portfolio story is identical either way and the account risk is zero. Dataset replay is the correct architecture for a safety research pipeline — you do not run known-adversarial prompts against a live model to demonstrate that your classifier works.

**Secondary: live Claude API mode** (optional, demo-only)
- Toggle flag in config, off by default
- Sends benign or mildly borderline prompts only — not AdvBench/JailbreakBench content
- Demonstrates the real-time pipeline for demo purposes; not part of the analytical story
- Cost: ~$1.20/day at 1 call/minute using Haiku 3.5; only enabled during active demos

---

## Escalation Logic (replaces confidence-threshold approach)

The 2×2 prompt + response verdict matrix:

| Prompt verdict | Response verdict | Escalation level |
|---|---|---|
| Benign | Safe | No escalation |
| Adversarial | Safe | Log only — model handled correctly |
| Benign | Unsafe | **High severity** — model introduced harm unprompted |
| Adversarial | Unsafe | **Critical** — jailbreak succeeded |

For prompt-only events (no response): escalate if adversarial with confidence > 0.7.

Disagreement escalation: if pair classifier and taxonomy classifier contradict each other (pair says safe, taxonomy flags a category, or vice versa), escalate as a model disagreement case at medium severity.

---

## Dashboard Changes

The existing five-tab dashboard structure is retained. Content changes per tab:

**StreamMonitor** — now shows prompt text (truncated) + response text (truncated), source dataset badge, and real-time verdict per model as a 3-column verdict row (pair: safe/unsafe, prompt: benign/adversarial, taxonomy: category badges)

**ModelPerformance** — now genuinely meaningful because ground truth is available for all streamed events (not just seeded data). F1, precision, recall computed against real labels in real time. Distribution shift framing carries over: compare live-stream F1 to held-out test-set F1 per dataset.

**ModelComparison** — now compares three qualitatively different classifiers, not three variants of the same task. The comparison story is: do they agree on which interactions are dangerous, and when they disagree, which one is right?

**Calibration** (new, from analysis-depth brief) — reliability diagrams, confidence distributions, agreement-confidence correlation. Now fully valid because ground truth is available for all events. This was the strongest analytical addition from the previous brief and is now properly grounded.

**HumanReview** — escalation queue now receives entries with a clear escalation reason from the 2×2 matrix (not just "model disagreement" or "low confidence"). Reviewers see: prompt, response, verdict from each model, and the escalation reason. Their decision (approve safe / confirm unsafe) is now meaningful label data.

---

## What Carries Over Unchanged

- Kafka infrastructure (topics, consumer groups, shadow routing)
- Async consumer base class (`BaseConsumer`)
- FastAPI application structure
- React dashboard skeleton (routing, tab structure, TanStack Query, component library)
- Postgres + Alembic (schema changes via new migration)
- case-queue escalation service (escalation reason strings change, core logic unchanged)
- All test infrastructure (pytest, vitest, conftest patterns)

---

## Success Criteria

1. Three models trained and evaluated on held-out splits: pair classifier, prompt adversarial detector, harm taxonomy classifier. Each with a reported F1 on the relevant test set.
2. Replay producer streams all four datasets through the classification pipeline at ~1 event/3 seconds. All five dashboard tabs render with real data.
3. The 2×2 escalation matrix routes at least three distinct escalation reason codes to the human review queue.
4. The Calibration tab shows a reliability diagram per model computed against real ground-truth labels — not a seeded-data approximation.
5. The ModelPerformance tab shows F1 computed against live-stream ground truth, not just seeded baseline.
6. Live Claude API mode works when toggled: sends a prompt, receives a response, classifies the pair, appears in the stream within 5 seconds.
7. One clearly articulable finding per model. Example: *"The pair classifier achieves F1=0.87 on HH-RLHF held-out data but drops to 0.74 on WildGuard — suggesting the harmlessness frame in HH-RLHF does not fully generalize to WildGuard's broader harm taxonomy."*

---

## Constraints

- Training must run on Apple M4 MPS (24GB unified memory). DistilBERT fine-tuning is confirmed safe at batch_size=128. Multi-label head follows the same pattern as train_detoxify.py.
- No proprietary or access-controlled data. All four datasets are publicly available on HuggingFace.
- Event schema must be backwards-compatible enough that the existing case-queue integration requires no changes.
- Live Claude API mode uses Haiku only — no Sonnet or Opus calls in the streaming path.
- AdvBench + JailbreakBench are small. Planner must assess whether ~6k balanced examples is sufficient for a binary prompt classifier or whether augmentation is required.

## Out of Scope

- Red-teaming or adversarial prompt generation (beyond replaying existing datasets)
- Model output correction or refusal generation
- Fine-tuning Claude or any generative model
- Multi-turn conversation handling (all events treated as single-turn)
- RLHF training loop (human review labels are collected but not used for retraining in v1)

## Open Questions for Planner

1. **Prompt classifier size**: ~6k balanced training examples may be too small for a standalone DistilBERT fine-tune to be credible. Should we augment with additional adversarial prompt datasets (e.g. HarmBench, SALAD-Bench), or accept the small training set with a strong held-out eval narrative?

2. **HH-RLHF input format**: the `chosen`/`rejected` field contains full conversation history as a formatted string. Does the pair classifier input use the full conversation or just the final assistant turn? Full conversation is more faithful to the dataset; final turn only is faster and easier to truncate to 512 tokens.

3. **WildGuard for both models**: WildGuard contributes to both the pair classifier and the taxonomy classifier. Does it get split by use (some examples for pair, others for taxonomy), or does it appear in both training sets? Overlap risks data leakage if the eval set is not carefully stratified.

4. **Replay producer mix**: the 60/25/10/5 dataset mix is an assumption. Should the mix be configurable at runtime via the dashboard (a "stream composition" control) or fixed in config? Configurable is more impressive as a demo feature but adds frontend complexity.

5. **`response_text` column**: adding a new column to `classifications` requires a new Alembic migration. Confirm this is the right approach vs storing the response in a separate `interactions` table with a foreign key.

## Handoff

Next role: planner

Reads this file plus `_config/project-state.md` for infrastructure context.

Planner must resolve all five open questions above before handing to implementer. The training pipeline order matters: pair classifier and prompt classifier should be trainable independently; taxonomy classifier depends on WildGuard allocation decision (Q3). Implementer should train in this order: pair classifier → prompt classifier → taxonomy classifier → replay producer → consumers → dashboard.

Update `project_learnings.md` to log the pivot from Bluesky toxicity to LLM safety classification.
