# Doc-Brief — Anthropic Safeguards Portfolio Writeups

## Audience

### Tier 1 — Technical (primary, deep-dive documents)

**Specific persona:** A software engineer on the Anthropic Safeguards Infrastructure team reviewing a job application. They read code daily, evaluate system design for correctness and scalability, and are specifically attuned to safety-domain reasoning. They are not a generalist hiring manager — they will follow a citation, check whether a design decision holds up under load, and notice if a stated tradeoff was not actually reasoned through. They do not need "what is Kafka" or "what is a classifier" explained. They will be sceptical of inflated claims and will respect honest scope-setting.

### Tier 3 — Executive / Stakeholder (primary, summary documents and overview)

**Specific persona:** A recruiter or hiring manager reviewing applications for the Anthropic Safeguards role. They read the portfolio before deciding whether to forward it to the engineering team. They have a general technical background but are not writing code. They need to understand: what was built, whether it is real and working, and whether it connects to the problems Anthropic is trying to solve. They make this decision in under five minutes. If the work is not immediately legible, they move on.

Secondary reader for the overview: same senior Safeguards engineer as above, using the overview as a navigation map before diving into individual projects.

---

## Goal

**Persuade** — the reader should finish each document believing the candidate has the technical depth, experimental rigour, and safety-domain thinking to contribute immediately to Safeguards Infrastructure work at Anthropic.

**For Tier 3 documents:** persuade the reader that the work is real, connected to the mission, and worth routing to engineers for a closer look.

Success for Tier 1: the reader can describe, from memory, one non-obvious design decision per project and one concrete result. They should not feel they were sold to.

Success for Tier 3: the reader understands what each project does, why it matters for AI safety, and what concrete evidence exists that it works. Under five minutes per document.

---

## Document Types and Placement

Seven documents in total. Write in this order:

### Group 1 — Portfolio Overview (one document)

| # | Type | Template | Audience | Placement |
|---|------|----------|----------|-----------|
| 1 | Portfolio Overview | `templates/technical-summary.md` (adapted) | Tier 2 + Tier 3 | `PORTFOLIO.md` at workspace root |

The overview is a single document that introduces the three-project system, the narrative arc, and links to each project. It is the landing page for both recruiters and engineers who discover the repository. It is not a technical deep-dive — it names the JD signals the work demonstrates and provides the framing that makes each project legible.

---

### Group 2 — Executive Summaries (one per project)

| # | Project | Type | Template | Placement |
|---|---------|------|----------|-----------|
| 2 | error-hide-seek | Executive Summary | `templates/executive-summary.md` | `projects/error-hide-seek/SUMMARY.md` |
| 3 | red-team-platform | Executive Summary | `templates/executive-summary.md` | `projects/red-team-platform/SUMMARY.md` |
| 4 | llm-safety-monitor | Executive Summary | `templates/executive-summary.md` | `projects/llm-safety-monitor/SUMMARY.md` |

Each is 300–500 words. Leads with the conclusion. Translates every technical claim into an outcome. Links to the Technical Deep-Dive for readers who want depth.

---

### Group 3 — Technical Deep-Dives (one per project)

| # | Project | Type | Template | Placement |
|---|---------|------|----------|-----------|
| 5 | error-hide-seek | Technical Deep-Dive | `templates/technical-deep-dive.md` | `projects/error-hide-seek/README.md` |
| 6 | red-team-platform | Technical Deep-Dive | `templates/technical-deep-dive.md` | `projects/red-team-platform/README.md` |
| 7 | llm-safety-monitor | Technical Deep-Dive | `templates/technical-deep-dive.md` | `projects/llm-safety-monitor/README.md` |

Each is 1000–2000 words. Dense, not padded. Each must stand alone.

---

## Source Material

**All documents:**
- `memory/project_anthropic_portfolio.md` — project status, all experimental results, key findings
- `memory/reference_anthropic_jd.md` — JD signals to demonstrate: eval metrics, review tooling, scalable safety defense, measurement systems

**error-hide-seek:**
- `projects/error-hide-seek/results/findings.md` — full experimental results, both experiments
- `projects/error-hide-seek/error_hide_seek/api/routers/sessions.py` — session creation and auto-annotation logic
- `projects/error-hide-seek/error_hide_seek/scoring/scorer.py` — scoring implementation

**red-team-platform:**
- `projects/red-team-platform/benchmarks/results.md` — Phase 1 sweep results, cluster summary

**llm-safety-monitor:**
- `resources/evals/llm-safety-monitor/pair-20260607T142119.json` — pair classifier eval results
- `resources/evals/llm-safety-monitor/prompt-20260607T142903.json` — prompt classifier eval results
- `resources/evals/llm-safety-monitor/taxonomy-20260607T143026.json` — taxonomy classifier eval results

---

## Key Messages

### Portfolio Overview

1. Three working, data-producing systems that compose into a single safety measurement and monitoring pipeline.
2. The narrative arc: the monitor provides real-time classification infrastructure; the red-team platform exposes it to live attack traffic; EHS measures what happens when humans and AI agents try to find errors together.
3. Each project demonstrates a different signal from the Safeguards Infrastructure JD: scalable safety defense (monitor), repeatable red-team tooling (red-team), and measurement of human+AI detection limits (EHS).
4. All three systems ran end-to-end with real data — Phase 1 red-team sweep (1,797 attacks, 6 strategies), EHS experiment 2 (100 papers, 67 human reviews), monitor classifiers evaluated on held-out splits.

---

### error-hide-seek

**Executive Summary key messages:**
1. A randomised controlled trial measuring whether Claude-quality AI hints improve human detection of planted errors in academic abstracts. The answer is no — overall uplift was −0.01 across both experiments.
2. The interesting finding is why: errors requiring domain knowledge or access to the original document (number substitution, false citation, causal inversion) are near-undetectable by any party without it — a fundamental constraint, not a model capability gap.
3. The system produced this result through a working RCT: 100 papers, three conditions (unaided / agent-only / human+agent), scored with TPR and FPR per category.
4. The work demonstrates rigorous experimental thinking in a safety-adjacent domain: honest null results, documented confounds, category-level analysis of what hint types actually help.

**Technical Deep-Dive key messages:**
1. The experiment is a proper three-condition RCT (unaided / agent-only / human+agent), not a demo — it produces a signed uplift number, not just "the agent helped."
2. The core finding is a detection ceiling driven by ground-truth access, not model capability: errors requiring the original document (number_substitution, false_citation, causal_inversion) are near-undetectable by any party without it.
3. The auto-annotation pipeline (POST /sessions triggers Claude, scores detections, saves HumanDetection rows) is the engineering centrepiece — it makes human review sessions comparable across conditions without manual intervention.
4. Uplift was −0.01 across both experiments: an honest null result. Claude-quality hints produced +0.33 uplift on inverted_conclusion (hint-responsive) and hurt performance on domain-dependent categories (noise-injection failure mode documented and interpreted).

---

### red-team-platform

**Executive Summary key messages:**
1. A platform that runs jailbreak attacks against a language model at scale, classifies results, clusters them by mechanism, and publishes events into the safety monitor pipeline in real time.
2. Phase 1 result: 1,797 attacks across 6 strategies revealed a clean two-cluster pattern — output-format and persona attacks bypass the model at near-100% success rate; suppression and combination attacks are blocked completely.
3. The platform is instrumented, not just executed: every attack produces a classified, clustered, published event, making results reproducible and composable with other monitoring systems.
4. The work demonstrates the infrastructure competency that the JD describes as "scalable safety defense": repeatable, data-producing, integrated with the monitoring layer.

**Technical Deep-Dive key messages:**
1. The platform operationalises a published attack corpus into a repeatable, instrumented sweep — each result is a classified, clustered, Kafka-published event, not just a pass/fail.
2. The two-cluster ASR pattern (bypass: gcg/evil_system_prompt/few_shot_json at ~1.0; blocked: refusal_suppression/combination_1/AIM at 0.0) is a concrete finding with a latency signature that explains the mechanism.
3. The outbox publisher creates a durable bridge between red-team results and the safety monitor — attacks that bypass the target model appear immediately in the monitor's classifier disagreement view.
4. Calibration was honest: original cost estimate was 6× off. The document explains the root causes (retry overhead, output-length-driven latency) and the corrected protocol.

---

### llm-safety-monitor

**Classifier F1 data (concrete, from held-out evaluation — use these numbers):**

| Classifier | F1 | Precision | Recall | Eval n |
|------------|-----|-----------|--------|--------|
| pair (response-level safety) | 0.549 | 0.393 | 0.910 | 6,337 |
| prompt (intent detection) | 0.818 | 0.752 | 0.897 | 2,512 |
| taxonomy (harm category) | 0.787 macro | — | — | 4,337 |

Taxonomy per-category F1 range: 0.584 (misinformation/material harm) to 0.945 (copyright violations). 13 categories total.

**Pair classifier framing (important):** The pair classifier's low precision (0.393) reflects a deliberate design choice: the escalation router treats any classifier disagreement as a signal, so the pair classifier is tuned for high recall (0.910) to avoid missing flagged responses. This is a safety-conservative design. The calibration shows a bimodal distribution (model outputs near-0 or near-0.5, not probabilistically distributed), which is a known property of binary fine-tuned DeBERTa at the decision boundary. The deep-dive must frame this explicitly — it is not a failure, it is the architecture doing what it is designed to do.

**Executive Summary key messages:**
1. A streaming Kafka pipeline that classifies every LLM interaction in real time across three independently trained classifiers — response-level safety, prompt intent, and harm taxonomy — before flagging disagreements for review.
2. The three classifiers ran on held-out evaluation sets: prompt classifier achieved F1 0.818 (2,512 samples), taxonomy classifier 0.787 macro across 13 harm categories, pair classifier 0.549 with 0.910 recall (deliberately recall-optimized).
3. The escalation router treats inter-classifier disagreement as signal — when the classifiers disagree, the interaction surfaces for review, anticipating that any single classifier will be wrong.
4. Red-team results from the attack platform flow directly into the monitor's event stream, making the three-project system a composable pipeline, not isolated demos.

**Technical Deep-Dive key messages:**
1. The monitor is a streaming Kafka pipeline — every LLM interaction is classified in real time by three independently fine-tuned classifiers (pair safety, prompt intent, harm taxonomy) before it reaches the dashboard.
2. The escalation router applies configurable thresholds across all three classifiers and routes disagreements to a review queue — the architecture anticipates that any single classifier will be wrong and treats inter-classifier conflict as signal.
3. Fine-tuning on HH-RLHF + WildGuard is a first-class artefact: the training pipeline, evaluation harness, and checkpoint management are documented and reproducible. Evaluated on held-out splits: prompt F1 0.818 (n=2,512), taxonomy F1 0.787 macro (n=4,337), pair recall 0.910 with precision 0.393 — recall-optimized by design for safety-conservative flagging.
4. The monitor is the infrastructure layer the other two projects depend on: red-team results flow through the outbox publisher into the monitor; EHS detections are architecturally compatible with the same path.

---

## Constraints

- **Length:** Overview 500–800 words. Executive Summaries 300–500 words each. Technical Deep-Dives 1000–2000 words each.
- **No generic claims:** Every claim must be backed by a specific number, decision, or design detail. "The system is scalable" without explanation is banned.
- **No apology framing for limitations:** Limitations state scope accurately. "EHS used a non-expert reviewer" is a scope note, not a failure. "Pair classifier precision is 0.393" is a design choice, not a weakness.
- **Grammatical person:** Third person by default. "We" when collaborative context is relevant. No first-person singular.
- **Punctuation:** No em-dashes, no semicolons. Commas and parenthetical clauses only.
- **No "In this post..." openers.** No section-summary conclusions.
- **Acronyms:** Define on first use.
- **Code blocks:** Only when a snippet conveys a design decision more efficiently than prose.
- **Tier 3 documents:** No inline code. Translate every technical statement into an outcome. One concept per sentence.

---

## Writing Order

Write documents in this sequence so the framing builds correctly:

1. `PORTFOLIO.md` — establishes the narrative arc all other documents assume
2. `projects/error-hide-seek/SUMMARY.md` — executive summary
3. `projects/error-hide-seek/README.md` — technical deep-dive (leads the portfolio)
4. `projects/red-team-platform/SUMMARY.md` — executive summary
5. `projects/red-team-platform/README.md` — technical deep-dive
6. `projects/llm-safety-monitor/SUMMARY.md` — executive summary
7. `projects/llm-safety-monitor/README.md` — technical deep-dive

---

## Handoff

The author reads this file plus the source material listed above. Write in order as listed above.

**Load template for each document type before writing it.** Executive Summaries use `templates/executive-summary.md`. Technical Deep-Dives use `templates/technical-deep-dive.md`. The overview adapts `templates/technical-summary.md` for a mixed-tier audience.

**Key risk — error-hide-seek:** The null uplift result (−0.01) could read as apologetic. It must not. It is the finding. The document should make a reader think "this is what rigorous measurement looks like."

**Key risk — red-team-platform:** The platform could read as "ran existing attacks against a model." The document must foreground the instrumentation (classifier integration, clustering, outbox publisher) over the attack execution itself.

**Key risk — llm-safety-monitor:** The pair classifier's low precision (0.393) must be framed as a deliberate recall-optimized design, not as a weakness. The three classifiers together, with inter-classifier disagreement as signal, is the architecture story — not any single F1 score in isolation.

**Key risk — all Tier 3 documents:** Every technical sentence must translate to an outcome. If a sentence requires technical background to interpret, it fails for this audience.
