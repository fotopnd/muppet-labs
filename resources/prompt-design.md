# prompt-design.md — LLM Prompt Conventions for Muppet Labs

> Load this file in the implementer role (when writing system prompts) and the reviewer role
> (to verify prompt semantic correctness). Do not load for projects that include no LLM features.

---

## Convention 1: Action labels must match system semantics

When a system prompt defines action labels (e.g. `approve`, `reject`, `escalate`), each label
must map to exactly what that action does in the codebase — specifically what the model,
enum, or status mapping says the label means.

**Before finalising any system prompt, check:**
- What does `approve` map to in `ACTION_TO_STATUS` (or equivalent)?
- What does `reject` map to?
- Does the prompt's definition of each label agree with that mapping?

**Why this matters:** In a T&S case queue, `approve` can mean "approve the content (it's fine)"
or "approve the removal (it's bad)." These are opposite. A one-word mislabel in a system prompt
silently inverts every decision the model makes. This class of bug does not appear in a code
review — the code is syntactically correct. It requires explicit prompt-level scrutiny.

**How to check:** Write out the action label chain:

```
prompt says "approve" means: [definition in prompt]
                        ↓
system maps approve →: [value in ACTION_TO_STATUS or equivalent]
                        ↓
UI shows / DB stores:  [what the user and downstream systems see]
```

All three must be consistent.

---

## Convention 2: Include a one-line worked example per action when the boundary is non-obvious

When action semantics are domain-specific or could be interpreted multiple ways, add a brief
example to the system prompt for each action. One sentence per action is enough.

```
- approve: Content does NOT violate policy. Example: "You're terrible at this game" — rude but not policy-violating.
- reject: Content clearly violates policy and should be removed. Example: Explicit slurs, direct threats, targeted harassment.
- escalate: Ambiguous or high-stakes. Example: Borderline threat with insufficient context to rule either way.
```

**Why this matters:** Models trained on diverse corpora will pattern-match to the most common
usage of a word. In a T&S context, "approve" and "reject" are not standard English usage —
they refer to case disposition, not content quality. Worked examples anchor the model to the
domain meaning, not the everyday meaning.

---

## Convention 3: Use `escalate` as the safe fallback, not `approve`

When a model is uncertain or a parse error occurs, the fallback action should be `escalate`
(route to human review), never `approve` (clear the case).

- `approve` as a fallback = bad content passes review silently.
- `escalate` as a fallback = a human sees it and makes the call.

In the classifier, parse failures and low-confidence results should both escalate. This is
already the pattern in `classifier.py` — maintain it in any future LLM feature.

---

## Reviewer Checklist (for projects with LLM prompts)

When reviewing code that includes a system prompt, add these checks to the standard review:

1. [ ] Action label definitions in the prompt match the system's action semantics (Convention 1 check above)
2. [ ] Worked examples are present for any action with non-obvious domain meaning (Convention 2)
3. [ ] Fallback / error path escalates rather than approves (Convention 3)
4. [ ] Parse error handling is tested or otherwise verified (does the classifier handle malformed JSON, fenced JSON, truncated output?)
