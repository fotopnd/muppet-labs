# Doc-Brief — Anthropic Safeguards Portfolio Writeups

## Audience

**Tier:** Technical (primary), Technical Leadership (secondary).

**Specific persona:** A software engineer on the Anthropic Safeguards Infrastructure team reviewing a job application. They read code daily, evaluate system design for correctness and scalability, and are specifically attuned to safety-domain reasoning. They are not a generalist hiring manager — they will follow a citation, check whether a design decision holds up under load, and notice if a stated tradeoff was not actually reasoned through. They do not need "what is Kafka" or "what is a classifier" explained. They will be sceptical of inflated claims and will respect honest scope-setting.

Secondary reader: a hiring manager with a technical background who reads the overview before deciding whether to pass the portfolio to engineers.

---

## Goal

**Persuade** — the reader should finish each document believing the candidate has the technical depth, experimental rigour, and safety-domain thinking to contribute immediately to Safeguards Infrastructure work at Anthropic.

Success: the reader can describe, from memory, one non-obvious design decision per project and one concrete result. They should not feel they were sold to.

---

## Document Type and Template

**Type:** Technical Deep-Dive (×3, one per project)
**Template:** `templates/technical-deep-dive.md`

Three documents, written in this order:
1. `error-hide-seek` — most complete data, most novel finding, leads the portfolio narrative
2. `red-team-platform` — provides the red-teaming context that motivates EHS
3. `llm-safety-monitor` — the infrastructure foundation; written last because it sets up the arc

Each document is the project's `README.md`, placed at the root of its project directory. Each must stand alone — a reader who lands on one project without context should not be confused.

---

## Source Material

**All three projects:**
- `memory/project_anthropic_portfolio.md` — project status, all experimental results, key findings
- `memory/reference_anthropic_jd.md` — JD signals to demonstrate: eval metrics, review tooling, scalable safety defense, measurement systems

**error-hide-seek:**
- `projects/error-hide-seek/results/findings.md` — full experimental results, both experiments
- `projects/error-hide-seek/error_hide_seek/api/routers/sessions.py` — session creation and auto-annotation logic
- `projects/error-hide-seek/error_hide_seek/scoring/scorer.py` — scoring implementation

**red-team-platform:**
- `projects/red-team-platform/benchmarks/results.md` — Phase 1 sweep results, cluster summary

**llm-safety-monitor:**
- Project tests and classifier architecture as known from project memory

---

## Key Messages

### error-hide-seek
1. The experiment is a proper three-condition RCT (unaided / agent-only / human+agent), not a demo — it produces a signed uplift number, not just "the agent helped."
2. The core finding is a detection ceiling driven by ground-truth access, not model capability: errors requiring the original document (number_substitution, false_citation, causal_inversion) are near-undetectable by any party without it.
3. The auto-annotation pipeline (POST /sessions triggers Claude, scores detections, saves HumanDetection rows) is the engineering centrepiece — it makes human review sessions comparable across conditions without manual intervention.
4. Uplift was −0.01 across both experiments: an honest null result. Claude-quality hints produced +0.33 uplift on inverted_conclusion (hint-responsive) and hurt performance on domain-dependent categories (noise-injection failure mode documented and interpreted).

### red-team-platform
1. The platform operationalises a published attack corpus into a repeatable, instrumented sweep — each result is a classified, clustered, Kafka-published event, not just a pass/fail.
2. The two-cluster ASR pattern (bypass: gcg/evil_system_prompt/few_shot_json at ~1.0; blocked: refusal_suppression/combination_1/AIM at 0.0) is a concrete finding with a latency signature that explains the mechanism.
3. The outbox publisher creates a durable bridge between red-team results and the safety monitor — attacks that bypass the target model appear immediately in the monitor's classifier disagreement view.
4. Calibration was honest: original cost estimate was 6× off. The document explains the root causes (retry overhead, output-length-driven latency) and the corrected protocol.

### llm-safety-monitor
1. The monitor is a streaming Kafka pipeline — every LLM interaction is classified in real time by three independently fine-tuned classifiers (pair safety, prompt intent, harm taxonomy) before it reaches the dashboard.
2. The escalation router applies configurable thresholds across all three classifiers and routes disagreements to a review queue — the architecture anticipates that any single classifier will be wrong and treats inter-classifier conflict as signal.
3. Fine-tuning on HH-RLHF + WildGuard is a first-class artefact: the training pipeline, evaluation harness, and checkpoint management are documented and reproducible, not one-off scripts.
4. The monitor is the infrastructure layer the other two projects depend on: red-team results flow through the outbox publisher into the monitor; EHS detections are architecturally compatible with the same path.

---

## Constraints

- **Length:** 1000–2000 words per document. Dense, not padded.
- **No generic claims:** Every claim must be backed by a specific number, decision, or design detail. "The system is scalable" without explanation is banned.
- **No apology framing for limitations:** Limitations state scope accurately. "EHS used a non-expert reviewer" is a scope note, not a failure.
- **Grammatical person:** Third person by default. "We" when collaborative context is relevant. No first-person singular.
- **Punctuation:** No em-dashes, no semicolons. Commas and parenthetical clauses only.
- **No "In this post..." openers.** No section-summary conclusions.
- **Acronyms:** Define on first use.
- **Code blocks:** Only when a snippet conveys a design decision more efficiently than prose.

---

## Handoff

The author reads this file plus the source material listed above. Write in order: error-hide-seek first, then red-team-platform, then llm-safety-monitor.

**Load template:** `templates/technical-deep-dive.md`

**Key risk — error-hide-seek:** The null uplift result (−0.01) could read as apologetic. It must not. It is the finding. The document should make a reader think "this is what rigorous measurement looks like."

**Key risk — red-team-platform:** The platform could read as "ran existing attacks against a model." The document must foreground the instrumentation (classifier integration, clustering, outbox publisher) over the attack execution itself.

**Key risk — llm-safety-monitor:** Without concrete F1 scores, this risks reading as architecture fiction. Ground every architectural claim in a specific test result, training detail, or observable behaviour.
