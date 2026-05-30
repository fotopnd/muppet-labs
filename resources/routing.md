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

## Sequence: `new-project-full`

**Objective:** Build a new project from scratch through working, reviewed code.
**Use when:** Starting something new with enough complexity to warrant full planning.
**Review gate:** After every role.

| Step | Role | Reads | Resources | Skills | Output |
|------|------|-------|-----------|--------|--------|
| 1 | `brief` | — | `vibecoding-style.md` | — | `roles/brief/output/output.md` |
| 2 | `planner` | `brief/output.md` | `vibecoding-style.md`, `[lang]-conventions.md` | setup skill if language decided | `roles/planner/output/output.md` |
| 3 | `architect` | `planner/output.md` | `[lang]-conventions.md` | — | `roles/architect/output/output.md` |
| 4 | `implementer` | `architect/output.md` | `[lang]-conventions.md`, `vibecoding-style.md` | relevant setup skill | `roles/implementer/output/output.md` |
| 5 | `reviewer` | `implementer/output.md` | `[lang]-conventions.md` | — | `roles/reviewer/output/output.md` |

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

> Reviewer focus in vibe mode: does it run, does it do the thing. Skip style and refactor unless obvious.

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

> Skip architect if the feature fits cleanly into existing structure. Human makes this call after reviewing planner output.

---

## Sequence: `debug-fix`

**Objective:** Diagnose a specific failure and produce a targeted fix.
**Use when:** Something is broken and needs diagnosis, not a full re-review.
**Review gate:** After debugger — confirm diagnosis before applying fix.

| Step | Role | Reads | Resources | Skills | Output |
|------|------|-------|-----------|--------|--------|
| 1 | `debugger` | Output of the role that produced the failure + error description from human | `[lang]-conventions.md`, `vibecoding-style.md` | — | `roles/debugger/output/output.md` |
| 2 | `implementer` (targeted) | `debugger/output.md` | `[lang]-conventions.md`, `vibecoding-style.md` | — | `roles/implementer/output/output.md` |

> Debugger output must contain: **Diagnosis** (what is failing and why), **Fix** (specific change required), **Verification** (how to confirm the fix worked).
> Implementer applies only the identified fix. Does not rewrite surrounding code.

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

> Architect describes target structure, not what to build from scratch. Reviewer focus: did behaviour stay the same, does output meet architectural intent.

---

## Sequence: `review-only`

**Objective:** Assess existing code without making changes.
**Use when:** Pre-commit review, quality check, or second-pass assessment.
**Review gate:** Output is the deliverable. No next role unless human initiates one.

| Step | Role | Reads | Resources | Skills | Output |
|------|------|-------|-----------|--------|--------|
| 1 | `reviewer` | `implementer/output.md` or code files from `project-state.md` | `[lang]-conventions.md` | — | `roles/reviewer/output/output.md` |

> Reviewer output must contain: **Correctness** (logic errors, edge cases, types), **Style** (convention deviations), **Tests** (gaps), **Refactor candidates** (notes only, no implementation).

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
