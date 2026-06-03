# Doc-Brief — moderation-stream one-pager

**Role:** doc-brief
**Sequence:** `write-doc` (step 1 of 3)
**Date:** 2026-06-02

---

## Audience

Tier 2 — Technical Leadership.

Specific persona: a hiring manager or staff engineer at Anthropic Safeguards who is technical enough to validate architectural choices but reviewing at the portfolio level — not reading code, reading decisions and outcomes.

---

## Goal

Inform.

The reader should understand what moderation-stream is, how it works at the system level, which design decisions shaped it, and what it demonstrates about the builder's technical judgment. Success means the reader walks away with a clear mental model of the architecture and a specific sense of the tradeoffs accepted.

---

## Document Type and Template

**Type:** Technical Summary
**Template:** `templates/technical-summary.md`
**Length target:** 500–700 words (one page)

---

## Source Material

- `roles/implementer/output/output.md` — file manifest, deviations, known gaps, how to run
- `roles/reviewer/output/output.md` — correctness findings, confirmed decisions
- `_config/project-state.md` — decisions log, architecture description

---

## Key Messages

1. **Real streaming architecture, not a batch simulation.** The pipeline uses Kafka with real consumer groups, per-consumer group IDs, and synchronous offset commits — not a batch job dressed as a stream.
2. **Five classifiers run in parallel on the same event stream**, accumulating per-message predictions against Jigsaw ground truth, enabling direct model comparison at equivalent input conditions.
3. **Phase-gated deployment.** Fine-tuned models are represented in the registry and dashboard from day one, activating through configuration change rather than code deployment when checkpoints are available.
4. **The domain is content moderation.** The Jigsaw Toxic Comment Classification dataset provides labeled ground truth; accuracy is computed against real labels, not synthetic benchmarks.
5. **End-to-end delivery in one session**, covering a streaming backend, async metrics API, and live React dashboard, all with tests.

---

## Constraints

- Maximum one page (~600 words body)
- No code blocks in the document body
- No em-dashes, no semicolons (voice rule)
- Do not name Anthropic or Safeguards as the intended employer — write for the work, not the application
- The reader knows what Kafka, FastAPI, and React are; define domain-specific terms (Jigsaw, percentile_cont) briefly inline
- Architecture section should be prose, not a diagram (markdown format)

---

## Handoff

The author reads this file plus the source material listed above.
Load template: `templates/technical-summary.md`
Key risk: the parallel-model comparison angle (key message 2) is the strongest differentiator — ensure it appears early and is not buried under infrastructure detail.
