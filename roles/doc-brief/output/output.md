# Doc-Brief — toxicity-classifier fine-tuning experiment

**Role:** doc-brief
**Sequence:** `write-doc` (step 1)
**Date:** 2026-06-03

---

## Audience

**Tier:** Technical (Tier 1), calibrated slightly toward Technical Leadership (Tier 2) for hiring context.

**Persona:** An ML engineer or AI safety engineer at Anthropic reviewing a portfolio project. Has deep familiarity with transformer fine-tuning, evaluation metrics, and production ML systems. Will read critically — not for reassurance, but to assess whether the author understands what they built and why. Will notice if the write-up skips over the interesting design decisions or glosses over limitations.

---

## Goal

**Inform / Educate** — the reader should understand what was built, why the design decisions were made, and what the results mean, clearly enough to assess the author's depth of understanding.

Success looks like: the reader finishes with a clear picture of (1) the experimental setup, (2) the results and what they demonstrate, (3) the non-obvious decisions and their tradeoffs, and (4) how the output connects to a downstream production system.

---

## Document Type and Template

**Type:** Technical Deep-Dive
**Template:** `templates/technical-deep-dive.md`

---

## Source Material

The author should read:
- `roles/model-trainer/output/output.md` — checkpoint paths, eval metrics, epoch log, downstream wiring
- `resources/evals/toxicity-classifier-finetuned/distilbert-finetuned-20260603T175950.json` — full eval results including per-category breakdown
- `projects/toxicity-classifier-finetuned/toxicity_classifier/train_distilbert.py` — training configuration decisions (warmup, eval strategy, load_best_model_at_end)
- `projects/toxicity-classifier-finetuned/toxicity_classifier/evaluate.py` — how zero-shot baseline is constructed and why it runs on CPU
- `projects/toxicity-classifier-finetuned/toxicity_classifier/device.py` — MPS device handling decisions
- `_config/project-state.md` — DistilBERT eval results section and session summary

---

## Key Messages

1. **Fine-tuning delivers a step-change improvement over zero-shot for safety classification.** F1 goes from 0.32 to 0.85 (+0.53) — this isn't a marginal gain; zero-shot is fundamentally unsuitable for production toxicity detection at this precision level.

2. **The model peaks at epoch 2 and overfits from epoch 3 onward.** Val loss rises (0.0804 → 0.1060) while train loss keeps falling. Early stopping via `load_best_model_at_end` is essential, not optional — without it, the deployed checkpoint would be measurably worse.

3. **AUC-ROC of 0.924 demonstrates strong discriminative power beyond the binary threshold.** The classifier's ranking ability is robust, which matters for severity scoring and threshold tuning in a real moderation pipeline.

4. **The fine-tuned model slots into a live Kafka-based moderation stream via a single env var.** No code changes — `DISTILBERT_CHECKPOINT_PATH` switches the consumer from zero-shot inference to the fine-tuned checkpoint. The architecture was designed to accommodate this handoff.

5. **Practical local training on Apple M4 MPS is viable for this class of model.** Full fine-tuning on 127k examples in ~3.5 hours without cloud GPU. The write-up should be honest about the constraints (no bf16, MPS pin_memory warning, batch size ceiling) so the reader can assess portability.

---

## Constraints

- **Length:** 1,000–1,800 words — dense enough to demonstrate depth, short enough to hold attention
- **RoBERTa:** Not yet trained — the write-up covers DistilBERT only. Do not speculate about RoBERTa results. Note that a second model is in progress.
- **No business case framing** — this is a technical audience; skip ROI language
- **Include the epoch log table** — the overfitting signal is one of the most technically interesting parts; make it visible
- **Acknowledge limitations honestly:** binary label only (Jigsaw has 6 categories), no calibration tuning, single training run (no hyperparameter search)
- **Link to repo** — assume the document will live in the project README or a portfolio page; reference `projects/toxicity-classifier-finetuned/` as the source

---

## Handoff

The author reads this file plus the source material listed above.
Load template: `templates/technical-deep-dive.md`

Key risk: The author may be tempted to pad the write-up with background on transformers or BERT architecture. The reader already knows this — skip it entirely and use the space for the non-obvious decisions (why epoch 2 is the best checkpoint, why zero-shot fails so badly on precision, why the consumer architecture was designed for hot-swapping).
