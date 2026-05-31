# routing.md — Muppet Labs Routing Sequences

> This file defines all named routing sequences. A sequence is an ordered chain of roles
> that together accomplish a specific objective. Load this file at the start of every session.
> The active sequence is recorded in `_config/project-state.md`.

---

## How to Use This File

1. Identify the objective for the current session.
2. Find the matching sequence in the table below.
3. Check `_config/project-state.md` to see which role was last completed.
4. Execute the next role in the sequence.
5. After each role completes and the human signs off, proceed to the next.

---

## The Retro Role

The `retro` role runs after a project or milestone is complete. It is not a project artefact —
its output feeds back into the workspace itself (`resources/`, `skills/`, `routing.md`).

**When retro is REQUIRED:** `new-project-full` — always run it. Every completed project should produce workspace improvements.

**When retro is RECOMMENDED:** `add-feature` (for substantial features), `refactor` (when the refactor revealed design issues).

**When retro is OPTIONAL:** `new-project-vibe` (fast builds — run it if the project surfaced something worth capturing), `debug-fix` (run it if the same bug class has appeared before or the fix revealed a systemic gap).

**When retro does NOT apply:** `review-only` — no implementation ran, nothing to reflect on.

**What retro reads:** `reviewer/output.md` + `implementer/output.md` + `_config/project-state.md` + `resources/routing.md` + `resources/vibecoding-style.md`. Load no language conventions files unless a specific finding requires them.

---

## Sequence: `new-project-full`

**Objective:** Build a new project from scratch through working, reviewed code.
**Use when:** Starting something new with enough complexity to warrant full planning.
**Review gate:** After every role.

| Step | Role | Reads | Resources | Skills | Output |
|------|------|-------|-----------|--------|--------|
| 1 | `brief` | — | `vibecoding-style.md` | — | `roles/brief/output/output.md` |
| 2 | `planner` | `brief/output.md` | `vibecoding-style.md`, `[lang]-conventions.md` | `setup-[lang]-project.md` if language decided | `roles/planner/output/output.md` |
| 3 | `architect` | `planner/output.md` | `[lang]-conventions.md` | — | `roles/architect/output/output.md` |
| 4 | `implementer` | `architect/output.md` | `[lang]-conventions.md`, `vibecoding-style.md` | `setup-[lang]-project.md` | `roles/implementer/output/output.md` |
| 5 | `reviewer` | `implementer/output.md` | `[lang]-conventions.md` | — | `roles/reviewer/output/output.md` |
| 6 | `retro` | `reviewer/output.md`, `implementer/output.md`, `project-state.md` | `vibecoding-style.md`, `routing.md` | — | `roles/retro/output/output.md` |

> **Plan mode note:** If plan mode ran before the sequence and produced a detailed architecture, the `architect` role may treat the plan file as pre-resolved planner output. It confirms decisions rather than re-deriving them. The architect should not duplicate what the plan already settled — validate and resolve open questions only.

> **Planner open questions convention:** When the planner raises open questions, each question should include a `Proposed answer:` inline. This lets the architect confirm or override rather than design from scratch.

---

## Sequence: `new-project-vibe`

**Objective:** Fast generative build. Collapse intake and planning into a single pass.
**Use when:** Exploring an idea quickly; output is draft-grade.
**Review gate:** After implementer and reviewer only. Brief→planner runs without a gate.

| Step | Role | Reads | Resources | Skills | Output |
|------|------|-------|-----------|--------|--------|
| 1 | `brief` + `planner` (combined) | — | `vibecoding-style.md`, `[lang]-conventions.md` | — | `roles/planner/output/output.md` |
| 2 | `implementer` | `planner/output.md` | `[lang]-conventions.md`, `vibecoding-style.md` | relevant setup skill | `roles/implementer/output/output.md` |
| 3 | `reviewer` (lightweight) | `implementer/output.md` | `[lang]-conventions.md` | — | `roles/reviewer/output/output.md` |
| 4 | `retro` *(optional)* | `reviewer/output.md`, `implementer/output.md`, `project-state.md` | `vibecoding-style.md`, `routing.md` | — | `roles/retro/output/output.md` |

> Reviewer focus in vibe mode: does it run, does it do the thing. Skip style and refactor unless obvious.
> Run retro if the vibe build surfaced a pattern or friction point worth capturing for future sessions.

---

## Sequence: `add-feature`

**Objective:** Add a well-defined feature to an existing project.
**Use when:** Project exists, architecture is settled, scope of addition is clear.
**Review gate:** After each role. Human decides whether to skip architect.

| Step | Role | Reads | Resources | Skills | Output |
|------|------|-------|-----------|--------|--------|
| 1 | `planner` | `_config/project-state.md` | `vibecoding-style.md`, `[lang]-conventions.md` | — | `roles/planner/output/output.md` |
| 2 | `architect` *(conditional)* | `planner/output.md` | `[lang]-conventions.md` | — | `roles/architect/output/output.md` |
| 3 | `implementer` | `architect/output.md` or `planner/output.md` if architect skipped | `[lang]-conventions.md`, `vibecoding-style.md` | — | `roles/implementer/output/output.md` |
| 4 | `reviewer` | `implementer/output.md` | `[lang]-conventions.md` | — | `roles/reviewer/output/output.md` |
| 5 | `retro` *(recommended for substantial features)* | `reviewer/output.md`, `implementer/output.md`, `project-state.md` | `vibecoding-style.md`, `routing.md` | — | `roles/retro/output/output.md` |

> Skip architect if the feature fits cleanly into existing structure. Human makes this call after reviewing planner output.
> Run retro when the feature was large enough to reveal friction in the existing architecture or workspace tooling.

---

## Sequence: `debug-fix`

**Objective:** Diagnose a specific failure and produce a targeted fix.
**Use when:** Something is broken and needs diagnosis, not a full re-review.
**Review gate:** After debugger — confirm diagnosis before applying fix.

| Step | Role | Reads | Resources | Skills | Output |
|------|------|-------|-----------|--------|--------|
| 1 | `debugger` | Output of the role that produced the failure + error description from human | `[lang]-conventions.md`, `vibecoding-style.md` | — | `roles/debugger/output/output.md` |
| 2 | `implementer` (targeted) | `debugger/output.md` | `[lang]-conventions.md`, `vibecoding-style.md` | — | `roles/implementer/output/output.md` |
| 3 | `retro` *(optional — run if bug class is likely to recur)* | `implementer/output.md`, `debugger/output.md`, `project-state.md` | `vibecoding-style.md`, `routing.md` | — | `roles/retro/output/output.md` |

> Debugger output must contain: **Diagnosis** (what is failing and why), **Fix** (specific change required), **Verification** (how to confirm the fix worked).
> Implementer applies only the identified fix. Does not rewrite surrounding code.
> Retro focus in debug-fix: did the bug reveal a gap in test coverage, a missing convention, or a recurring pattern? If the same class of bug has appeared before, retro is high-value.

---

## Sequence: `refactor`

**Objective:** Restructure existing code for clarity, maintainability, or performance.
**Constraint:** Behaviour must not change.
**Review gate:** After architect — confirm direction before touching code.

| Step | Role | Reads | Resources | Skills | Output |
|------|------|-------|-----------|--------|--------|
| 1 | `architect` | `implementer/output.md` or code files from `project-state.md` | `[lang]-conventions.md` | — | `roles/architect/output/output.md` |
| 2 | `implementer` | `architect/output.md` | `[lang]-conventions.md`, `vibecoding-style.md` | — | `roles/implementer/output/output.md` |
| 3 | `reviewer` | `implementer/output.md` | `[lang]-conventions.md` | — | `roles/reviewer/output/output.md` |
| 4 | `retro` *(recommended)* | `reviewer/output.md`, `implementer/output.md`, `project-state.md` | `vibecoding-style.md`, `routing.md` | — | `roles/retro/output/output.md` |

> Architect describes target structure, not what to build from scratch. Reviewer focus: did behaviour stay the same, does output meet architectural intent.
> Retro focus in refactor: did the refactor reveal design debt worth recording? Did the process surface a convention that should be codified? Refactors are high-signal for workspace improvements.

---

## Sequence: `review-only`

**Objective:** Assess existing code without making changes.
**Use when:** Pre-commit review, quality check, or second-pass assessment.
**Review gate:** Output is the deliverable. No next role unless human initiates one.

| Step | Role | Reads | Resources | Skills | Output |
|------|------|-------|-----------|--------|--------|
| 1 | `reviewer` | `implementer/output.md` or code files from `project-state.md` | `[lang]-conventions.md` | — | `roles/reviewer/output/output.md` |

> Reviewer output must contain: **Correctness** (logic errors, edge cases, types), **Style** (convention deviations), **Tests** (gaps), **Refactor candidates** (notes only, no implementation).
> Retro does not apply to `review-only` — no implementation ran and no workspace friction was generated.

---

## Adding New Sequences

Append a new section using this format:

```markdown
## Sequence: `sequence-name`

**Objective:** [what this accomplishes]
**Use when:** [when to choose this over other sequences]
**Review gate:** [when the human reviews]

| Step | Role | Reads | Resources | Skills | Output |
|------|------|-------|-----------|--------|--------|
| 1 | `role-name` | [input files] | [resource files] | [skill files or —] | [output path] |
```
