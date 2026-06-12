# Brief — Classifier Self-Red-Team

**Sequence:** `new-project-full` | **Role:** brief | **Step:** 1 of N  
**Date:** 2026-06-12

---

## Project Name

classifier-self-redteam

---

## Description

A targeted evaluation that red-teams the pair safety classifier itself — finding inputs that are semantically harmful but evade the classifier's detection — in order to measure and document the classifier's blind spots and demonstrate honest self-critique of the monitoring infrastructure.

---

## Language(s)

Python (new evaluation scripts within llm-safety-monitor-training or as a standalone eval project)

---

## Success Criteria

1. An evasion corpus is constructed: for each of ≥5 evasion strategies, ≥20 examples of harmful content that the pair classifier scores as safe (predicted_label=0)
2. Evasion strategies tested include at minimum: synonym substitution, passive-voice reframing, embedding harmful content in fictional framing, code-switching (mid-sentence language switch), and indirect/euphemistic phrasing
3. A scorer measures and reports: per-strategy evasion rate (fraction of attempts classified as safe), confidence distribution on evaded examples
4. Baseline comparison: the same harmful inputs in unmodified form are scored by the classifier, confirming they would normally be flagged (evasion delta is measurable)
5. Results written to `benchmarks/classifier-evasion.md` with a per-strategy table
6. At least one finding is incorporated back into the LLM Safety Monitor SUMMARY.md as a known limitation with honest framing

---

## Constraints

- The pair classifier checkpoint is fixed — this is evaluation only, no retraining in scope
- Evasion corpus is authored with LLM assistance (Claude generates variants; human reviews for actual harmfulness)
- No white-box attacks (no gradient access) — black-box evasion only, matching real-world threat model
- Must use the existing `llm-safety-classifier` package's inference interface (no direct model access)
- Harmful content in the corpus must stay within the categories already covered by the red-team corpus (no new harm categories introduced)

---

## Out of Scope

- Adversarial training or classifier retraining based on findings (out of scope for v1)
- White-box / gradient-based attacks (FGSM, PGD, etc.)
- Evasion of the prompt or taxonomy classifiers (pair classifier only in v1)
- Automated evasion search (genetic algorithms, etc.) — manual + LLM-assisted authoring only

---

## Assumptions

- The pair classifier has meaningful blind spots on at least some evasion strategies — confirmed plausible given F1=0.549 and recall-biased training
- Claude can generate plausible harmful content variants for evaluation purposes within the scope of the existing red-team corpus (authorized safety research context)
- Evasion rate will vary by strategy — some strategies will be more effective than others, producing a non-trivial results table

---

## Handoff

Next role: planner  
The planner must decide: standalone project vs addition to llm-safety-monitor-training; whether to store evasion corpus as a CSV or in the existing DB; how to handle the content moderation of the evasion corpus itself (Claude-generated harmful variants need human review before storage). Flag the content authoring step as requiring human sign-off.
