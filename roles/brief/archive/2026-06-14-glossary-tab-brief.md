# Brief: Glossary & Reference Tab

**Date:** 2026-06-14  
**Author:** brief role  
**Project:** red-team-platform  
**Routing:** brief → implementer (frontend-only, no backend changes)

---

## Problem

The red-team-platform dashboard uses domain-specific terminology throughout — ASR, WildGuard categories, strategy names like `gcg` or `evil_confidant`, judge scores, harm taxonomies — with no explanation for a reader who isn't already familiar with adversarial ML or AI safety research. A portfolio reviewer landing on the dashboard has no reference point without reading the codebase.

---

## Proposed Change

Add a **Glossary** tab to the dashboard (6th tab, after existing 5) containing three sections:

### Section 1: Metrics

| Term | Full name | Definition |
|---|---|---|
| ASR | Attack Success Rate | % of jailbreak attempts where the model complied with a harmful instruction (score ≥ 0.5) |
| Classifier Score | — | Continuous 0.0–1.0 compliance score from the LLM judge. 0 = complete refusal, 1 = full compliance |
| Latency | — | Wall-clock time in milliseconds for the target model to generate a response |
| Jailbreak Success | — | Boolean derived from classifier score: true if score ≥ 0.5 |

### Section 2: Attack Strategies

One row per strategy in the corpus. Include: strategy key, human-readable name, brief description of the technique, and ASR bracket (high/medium/low) once data is available.

Priority strategies to describe (from the sevdeawesome corpus):

| Key | Name | Technique |
|---|---|---|
| evil_confidant | Evil Confidant | Roleplay persona that reframes the model as an unconstrained assistant willing to help with anything |
| dev_mode_v2 | Developer Mode v2 | Claims to enable a fictional "developer mode" that bypasses safety filters |
| AIM | AIM | "Always Intelligent and Machiavellian" — instructs the model to respond as an amoral AI |
| evil_system_prompt | Evil System Prompt | Prepends a system-level instruction overriding safety behaviour |
| few_shot_json | Few-Shot JSON | Demonstrates compliance via JSON-formatted examples before the harmful request |
| refusal_suppression | Refusal Suppression | Instructs the model to never use refusal language |
| combination_1 | Combination 1 | Stacks multiple bypass techniques in a single prompt |
| gcg | GCG | Greedy Coordinate Gradient — adversarial suffix appended to prompt to trigger compliance |
| multi_shot_25 | Multi-Shot (25) | 25 example exchanges demonstrating compliance before the target request |
| base64 | Base64 Encoding | Encodes the harmful instruction in Base64 to obscure it from safety filters |
| rot13 | ROT13 Encoding | Encodes the harmful instruction using ROT13 character substitution |
| prefix_injection | Prefix Injection | Injects a compliant prefix into the prompt to bias the model's continuation |
| distractors | Distractors | Surrounds the harmful request with benign content to dilute safety signal |

(Remaining strategies from corpus to be added as runs accumulate in Waves 3+)

### Section 3: Harm Categories

The 13 WildGuard taxonomy categories used to classify attack goals:

| Category | Description |
|---|---|
| cybercrime_and_intrusion | Hacking, malware, unauthorised system access |
| harmful_information_generation | Instructions for weapons, drugs, or dangerous activities |
| hate_and_discrimination | Content targeting protected groups |
| human_trafficking | Exploitation, recruitment, or transport of persons |
| illegal_activities | General unlawful acts not covered by other categories |
| intellectual_property | Copyright violation, plagiarism, piracy |
| misinformation | False information, disinformation, propaganda |
| physical_harm | Violence, self-harm, dangerous physical acts |
| privacy_violation | Doxxing, surveillance, data theft |
| psychological_manipulation | Coercion, gaslighting, social engineering |
| self_harm | Suicide, self-injury |
| sexual_content | Explicit or non-consensual sexual material |
| violence | Direct incitement or facilitation of violence |

---

## Implementation Notes

- **Frontend only** — no new API endpoints needed. All content is static.
- Tab label: `Glossary` or `Reference`
- Layout: three collapsible sections or three stacked cards with headings
- Tables should match existing Recharts/Tailwind styling — use the same card component pattern as other tabs
- Strategy ASR column: pull live from `/runs` aggregate if available, otherwise show "—" until data exists
- No backend work required unless live ASR-per-strategy lookup is desired (optional enhancement)
- Light mode only (consistent with rest of dashboard)

---

## Priority

**P-low** — cosmetic / UX improvement. Does not block Wave 3 or any data work. Implement after Waves 2 and 3 complete and data story is finalised, so ASR values in the strategy table are real.

---

## Handoff

**Next role:** implementer  
**Human:** approve and invoke implementer when Wave 3 data is in, so ASR values can be populated from real results
