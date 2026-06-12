# Author Output — toxicity-classifier fine-tuning experiment

**Role:** author
**Sequence:** `write-doc` (step 2)
**Date:** 2026-06-03

---

## Document Written

**File:** `projects/toxicity-classifier-finetuned/docs/distilbert-finetuning-experiment.md`
**Type:** Technical Deep-Dive
**Template:** `templates/technical-deep-dive.md`
**Word count:** ~1,500 words

---

## Handoff

**Next role:** doc-reviewer

Read `roles/doc-brief/output/output.md` for the key messages to verify, and `resources/writing-voice.md` for voice enforcement.

Key messages to check:
1. Zero-shot precision failure (0.21) clearly motivated — not buried
2. Epoch 2 overfitting signal visible in the table and explained in the text
3. AUC-ROC 0.924 interpreted, not just reported
4. Env-var activation pattern explained with enough specificity
5. MPS constraints (bf16, pin_memory) stated honestly without apology

Voice checks to enforce:
- No em-dashes or semicolons
- "Though" not "but" for concessive points
- Third person throughout
- No transformer background padding
