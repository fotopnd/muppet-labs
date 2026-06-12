# routing.md — Muppet Labs Routing Sequences

> This file defines all named routing sequences. A sequence is an ordered chain of roles
> that together accomplish a specific objective. Load this file at the start of every session.
> The active sequence is recorded in `_config/project-state.md`.

---

## How to Use This File

1. Identify the objective for the current session.
2. Find the matching sequence in the table below.
3. Check `_config/project-state.md` to see which role was last completed.
4. **Before executing any role:** load the language conventions file(s) for every language in the project (`resources/[lang]-conventions.md`). Check the sequence table's Resources column — if it lists `[lang]-conventions.md`, it is required, not optional. Do not skip this even if the language seems familiar.
5. Execute the next role in the sequence.
6. After each role completes and the human signs off, proceed to the next.

> **In-flight sequence check:** At the start of every session, check `project-state.md` for any
> sequence currently in-flight. If a sequence is in-flight, the next role in that sequence must
> run before new work begins — unless the human explicitly overrides. Do not start a new feature
> or project while a prior sequence is paused mid-run.

> **Role output archiving:** Before overwriting any `roles/[role]/output/output.md`, copy the existing file to `roles/[role]/archive/[date]-[project-name]-output.md`. Example: `roles/brief/archive/2026-05-31-eval-harness-output.md`. The `output/output.md` is a shared scratch space; `archive/` is the permanent record.

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
| 4 | `design-brief` *(if project has frontend)* | `planner/output.md`, `architect/output.md` | `design_style.md`, `vibecoding-style.md` | — | `roles/design-brief/output/output.md` |
| 5 | `frontend-architect` *(if project has frontend)* | `design-brief/output.md`, `architect/output.md` | `design_style.md`, `[lang]-conventions.md` | `setup-design-tokens.md` (new projects) | `roles/frontend-architect/output/output.md` |

> **frontend-architect context note:** Do not load `vibecoding-style.md` — it is not referenced in layout decisions and was already loaded by design-brief. Load only `design_style.md` and the language conventions file.
| 6a | `implementer` **(backend phase)** *(full-stack projects only)* | `architect/output.md` | `python-conventions.md`, `vibecoding-style.md` | `setup-uv-project.md` | `roles/implementer/output/backend-output.md` |
| 6b | `implementer` **(frontend phase)** *(full-stack projects only)* | `implementer/output/backend-output.md`, `frontend-architect/output.md` or `architect/output.md` | `typescript-conventions.md`, `vibecoding-style.md` | `setup-ts-pnpm.md` | `roles/implementer/output/output.md` |
| 6 | `implementer` **(single-language projects)** | `architect/output.md` | `[lang]-conventions.md`, `vibecoding-style.md` | `setup-[lang]-project.md` | `roles/implementer/output/output.md` |
| 7 | `ui-reviewer` *(if project has frontend)* | `implementer/output.md`, `frontend-architect/output.md`, `design-brief/output.md` | `design_style.md` | — | `roles/ui-reviewer/output/output.md` |
| 8 | `reviewer` | `implementer/output.md` | `[lang]-conventions.md`, `prompt-design.md` (if project includes LLM prompts) | — | `roles/reviewer/output/output.md` |
| 9 | `retro` | `reviewer/output.md`, `implementer/output.md`, `project-state.md` | `vibecoding-style.md`, `routing.md` | — | `roles/retro/output/output.md` |

> **Full-stack implementer phasing (steps 6a/6b):** For projects with both a Python backend and a TypeScript frontend, run step 6a first. The backend phase ends when `backend-output.md` is written and linting is clean. Human reviews and signs off. Then step 6b runs — frontend only — reading `backend-output.md` as its primary input. The final `output.md` (written by 6b) summarises both phases and is the file the reviewer reads. Step 6 (single row) applies to single-language projects only.

> **UI debug loop:** If `ui-reviewer` returns REWORK NEEDED, `ui-debugger` applies fixes, then `ui-reviewer` runs a second pass before `reviewer` proceeds.

> **Plan mode note:** If plan mode ran before the sequence and produced a detailed architecture, the `architect` role may treat the plan file as pre-resolved planner output. It confirms decisions rather than re-deriving them. The architect should not duplicate what the plan already settled — validate and resolve open questions only.

> **Architect consolidation rule:** If this is a delta architect pass (extending a prior output), the architect must consolidate the prior output and the delta into a single complete spec in `roles/architect/output/output.md` before archiving. The implementer reads one file — never a diff + base. Diffs belong in the architect's working notes; the handoff file must be self-contained.

> **Planner open questions convention:** When the planner raises open questions, each question should include a `Proposed answer:` inline. This lets the architect confirm or override rather than design from scratch.

> **Markdown-only deliverables:** When the project output is Markdown only (e.g. a workspace role definition, a design document), planner, architect, and implementer should not load language conventions files — there is no code to lint or type-check. Use the `new-role` sequence instead if the deliverable is a workspace role.

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
| 3 | `design-brief` *(if feature has UI)* | `planner/output.md`, `architect/output.md` | `design_style.md` | — | `roles/design-brief/output/output.md` |
| 4 | `frontend-architect` *(if feature has UI)* | `design-brief/output.md`, `architect/output.md` | `design_style.md`, `[lang]-conventions.md` | — | `roles/frontend-architect/output/output.md` |
| 5 | `implementer` | `frontend-architect/output.md` + `architect/output.md`, or `architect/output.md` only if no UI | `[lang]-conventions.md`, `vibecoding-style.md` | — | `roles/implementer/output/output.md` |
| 6 | `ui-reviewer` *(if feature has UI)* | `implementer/output.md`, `frontend-architect/output.md`, `design-brief/output.md` | `design_style.md` | — | `roles/ui-reviewer/output/output.md` |
| 7 | `reviewer` | `implementer/output.md` | `[lang]-conventions.md`, `prompt-design.md` (if project includes LLM prompts) | — | `roles/reviewer/output/output.md` |
| 8 | `retro` | `reviewer/output.md`, `implementer/output.md`, `project-state.md` | `vibecoding-style.md`, `routing.md` | — | `roles/retro/output/output.md` |

> Skip architect if the feature fits cleanly into existing structure. Human makes this call after reviewing planner output.
> UI debug loop: if `ui-reviewer` returns REWORK NEEDED, `ui-debugger` applies fixes, then `ui-reviewer` runs a second pass before `reviewer` proceeds.

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

## Sequence: `write-doc`

**Objective:** Produce a reviewed, edited document about a project for a specific audience and goal.
**Use when:** A project exists and a written deliverable is needed — portfolio piece, technical summary, stakeholder update, blog post, or any other document type in `resources/doc-types.md`.
**Review gate:** After `doc-brief` (confirm audience/goal/type before any writing); after `doc-reviewer` (editorial pass complete).

| Step | Role | Reads | Resources | Skills | Output |
|------|------|-------|-----------|--------|--------|
| 1 | `doc-brief` | `project-state.md` + project role outputs (human specifies) | `audience-tiers.md`, `doc-types.md` | — | `roles/doc-brief/output/output.md` |
| 2 | `author` | `doc-brief/output.md`, template, project materials listed in brief | `audience-tiers.md`, `writing-voice.md` | — | `projects/[name]/docs/[doc-name].md` + `roles/author/output/output.md` |
| 3 | `doc-reviewer` | `doc-brief/output.md`, document | `audience-tiers.md`, `writing-voice.md` | — | document edited in-place + `roles/doc-reviewer/output/output.md` |

> **Verdict: READY** — document is done. No new files created.
> **Verdict: AUTHOR REWORK NEEDED** — author addresses `[AUTHOR: ...]` flags in the document, then doc-reviewer does a second pass on the same file. No new file created.
> **Retro does not apply** to `write-doc`. Writing sessions are short-cycle and do not generate workspace tooling friction.

---

## Sequence: `design-diagram`

**Objective:** Produce a reviewed, audience-calibrated diagram embedded in an existing document.
**Use when:** A document references architecture, data flow, or a system structure that prose cannot convey efficiently. The target document already exists; the diagram is added to it.
**Review gate:** After `diagram-brief` (confirm scope and Must Show list before drawing); after `diagram-reviewer` (confirm the diagram is correct and legible).

| Step | Role | Reads | Resources | Output |
|------|------|-------|-----------|--------|
| 1 | `diagram-brief` | Target document + source materials | `audience-tiers.md`, `diagram-types.md` | `roles/diagram-brief/output/output.md` |
| 2 | `diagram-author` | `diagram-brief/output.md` + target document | `diagram-types.md`, `audience-tiers.md` | Diagram embedded in target document + `roles/diagram-author/output/output.md` |
| 3 | `diagram-reviewer` | `diagram-brief/output.md` + target document | `audience-tiers.md` | Diagram edited in-place + `roles/diagram-reviewer/output/output.md` |

> **One diagram per run.** If a document needs multiple diagrams, run the full sequence once per diagram. Archive `diagram-brief/output.md` between runs.
> **No new files.** The author edits the target document in-place. The diagram-reviewer edits the same file. No versioned copies are created.
> **Retro does not apply** to `design-diagram`. Diagram sessions are short-cycle and do not generate workspace tooling friction.

---

## The Daily Brief Role

The `daily-brief` role is a session-start orientation. It is not part of any sequence — it can
be invoked at any time, independently of whatever sequence is in-flight.

**When to use:** At the start of any session where you want to orient before picking up work.
Ask: "what should we work on?" or "run the daily brief" and it will synthesise current project
state, priorities, and the ideas queue into a short actionable brief.

**What it reads:** `resources/priorities.md` + `resources/project-status.md` +
`_config/project-state.md` + `resources/project_ideas.md`

**What it produces:** `roles/daily-brief/output/output.md` — a ~30–50 line brief with
per-project next actions and the top candidate from the ideas queue.

**It does not gate work.** After the brief, the human decides what to do next and which
sequence (if any) to start.

> Keep `resources/priorities.md` up to date. The brief is only as useful as that file is current.

---

## Sequence: `new-role`

**Objective:** Create a new reusable workspace role (`CONTEXT.md` + blank output template).
**Use when:** Adding a role that does not exist yet. The deliverable is Markdown only — no source code is produced.
**Review gate:** After architect (confirm spec before writing the contract); after reviewer.

| Step | Role | Reads | Resources | Skills | Output |
|------|------|-------|-----------|--------|--------|
| 1 | `brief` | — | `vibecoding-style.md` | — | `roles/brief/output/output.md` |
| 2 | `planner` | `brief/output.md` | `vibecoding-style.md` | — | `roles/planner/output/output.md` |
| 3 | `architect` | `planner/output.md` | — | — | `roles/architect/output/output.md` |
| 4 | `implementer` | `architect/output.md` | `vibecoding-style.md` | — | `roles/implementer/output/output.md` |
| 5 | `reviewer` | `implementer/output.md` + produced files | — | — | `roles/reviewer/output/output.md` |
| 6 | `retro` | `reviewer/output.md`, `implementer/output.md`, `project-state.md` | `vibecoding-style.md`, `routing.md` | — | `roles/retro/output/output.md` |

> **No language conventions files** are loaded at any step — the deliverable is Markdown.
> **Architect generalisation check:** Before writing the CONTEXT.md spec, confirm the role contract would work unchanged on a project with a completely different dataset, task, and model family. Any project-specific detail must become an input field.
> **Implementer deliverables:** `roles/<role-name>/CONTEXT.md` and `roles/<role-name>/output/output.md` (blank template). No source code.

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
