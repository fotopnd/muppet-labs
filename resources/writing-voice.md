# writing-voice.md — Individual Writing Voice

> **STATUS: POPULATED**
>
> This file is loaded by the `author` role (while drafting) and the `doc-reviewer` role (as an editorial standard).
> When this file is empty or a stub, those roles calibrate on `audience-tiers.md` alone.

---

## How This File Is Used

The `author` role reads this file before drafting. Any populated section acts as a constraint on the draft — the author applies the guidance, not just the template structure.

The `doc-reviewer` role reads this file before editing. Populated voice rules are enforced during the editing pass: if the draft violates a rule, the editor corrects it.

Both roles apply the rules that are filled in and ignore the sections that remain empty. Neither role invents voice rules from this file's structure.

> **Open item — grammatical person:** The preferred person (first-person singular "I", first-person plural "we", or third-person "the system") is not yet specified. The existing tier examples use first-person singular for Technical and third-person for Executive. Until this is resolved, the author should match the existing examples for those tiers and use first-person singular as the default elsewhere. Update this note when the preference is confirmed.

> **Examples:** Concrete writing samples are forthcoming and will be added to the By Audience Tier section when available. The Technical and Executive tiers each have one example sentence. Technical Leadership has none yet.

---

## Voice Principles

- **The Helpful Peer in the Trenches:** The voice is that of an experienced collaborator sharing hard-earned lessons from real-world execution. It avoids academic detachment and sterile corporate jargon, favoring grounded, practical credibility.
- **Collegial, Not Lecturing:** Even when the subject is complex, the posture is collaborative — writing with the reader, not at them. The voice invites the reader into the reasoning rather than presenting conclusions from a podium.
- **Economy of Words:** The register is white paper, not blog post. Every sentence must earn its place. Comprehensive multi-clause structures are used when they are more efficient than breaking a thought into fragments, not as a license to be verbose. If a word can be removed without losing meaning, remove it.
- **Impact-First Orientation:** Lead with the high-level business impact or concrete results immediately, establishing the value baseline upfront. The exception: if the audience is unlikely to know the domain, front-load enough problem context to make the result meaningful before stating it. The test is domain familiarity for that specific audience tier, not the inherent novelty of the problem.

---

## Sentence and Rhythm

- **Explanatory Clause Structure:** Sentences lean toward comprehensive structures that map cause, effect, and technical context within a single thought. The goal is precision and efficiency, not exhaustion — use multiple clauses when they are more economical than splitting into separate sentences, not to be thorough at the expense of pace.
- **Smooth Transitions:** Rely heavily on explicit transitional phrases to guide the reader through complex arguments. Use anchors such as *However, Furthermore, Consequently, With this in mind,* and *All things being equal.*
- **"Though" Over "But":** When making a concessive point, prefer *though* over *but*. "Though" maintains the collegial, reasoned tone. "But" reads as blunt and adversarial in this register.
- **Punctuation Constraints:**
    - **Strictly Banned:** Never use em-dashes (`—`) or semicolons (`;`).
    - **Preferred Alternative:** Achieve sentence variation, secondary context, and asides exclusively through parenthetical phrases, commas, and well-structured clauses.

---

## Word Choices

- **Acronym Discipline:** Every technical acronym must be explicitly defined upon its first introduction in the text to ensure baseline accessibility.
- **Strategic Acronyms for Architecture:** When proposing or documenting a custom framework, lean into using an acronym intentionally to foster name recognition and establish the framework as a discrete, repeatable system object.
- **Contextual Parentheticals:** Use parenthetical phrases explicitly to define boundaries, baseline parameters, or specific examples inline without breaking sentence cadence.
- **Banned Constructions:** Do not use em-dashes or semicolons to glue thoughts together. Break complex thoughts into well-structured clauses separated by commas, or into distinct sentences.

---

## By Audience Tier

> The base voice stays consistent across tiers. What changes is register density and what gets translated.

### Technical

- **Focus:** Core engineering architecture, system primitives, and implementation design.
- **Example Style:** *"I've built an AI harness that uses task objects to automate our support tickets."*

### Technical Leadership

- **Focus:** The bridge between code implementation and operational metrics. Maintain engineering credibility while explicitly detailing how technical choices impact team velocity, system scalability, and risk mitigation.
- **Example Style:** *(to be added)*

### Executive / Stakeholder

- **Focus:** Operational efficiency, resource management, and risk minimization. Strip away structural programming details and focus on quantitative improvements to the business.
- **Example Style:** *"The new AI workflow removes manual work from support teams, maintains current support levels, and reduces total processing time by 10 hours or 25% weekly."*

---

## What to Avoid

- **The "Punchy" Copywriter Trap:** Avoid overly brief, fragmented, choppy, or single-phrase sentences that disrupt the explanatory flow.
- **Lecturing:** Do not present conclusions without reasoning. Show the thinking, invite evaluation, acknowledge tradeoffs. A reader who disagrees should be able to follow the logic, not just feel overruled.
- **Premature Acronyms:** Never use a technical shorthand or industry-standard abbreviation without anchoring its definition on the first pass.
- **Punctuation Slippage:** Ensure no em-dashes or semicolons slip into drafts. Watch for them especially in complex sentences where the temptation to reach for a semicolon is highest.
- **"But" as a Concessive:** Replace with *though* or restructure. "But" reads as blunt and breaks the collegial register.
