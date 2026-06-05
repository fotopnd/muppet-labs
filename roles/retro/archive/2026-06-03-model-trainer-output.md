# Retro — model-trainer

**Role:** retro
**Sequence:** `new-project-full` (step 9)
**Date:** 2026-06-03

---

## Project

`model-trainer` workspace role. Sequence: `new-project-full`. One session (2026-06-03). Roles that ran: planner → architect → architect (revised) → implementer → reviewer (with post-review fixes) → retro.

---

## What Went Well

**`dataset_env_var` as the generalisation lever.**
The brief specified "generic enough to be reused across model architectures" but didn't identify the mechanism. The architect found it: decoupling the dataset env var name from the role contract. This is the kind of structural decision the architect role is meant to make — abstract an interface, not a specific use case. Worth noting as a pattern: when a role needs to be project-agnostic, look for the concrete point of coupling (in this case, an env var name) and make it an input.

**Reviewer findings were additive only.**
All three reviewer findings were Notes additions — no restructuring, no interface changes. This means the architect spec was precise enough that the implementer produced a clean first pass. The architect's decision to resolve all four open questions before handing off to the implementer removed ambiguity that would otherwise have appeared as reviewer blockers.

**Memory file from project 8 accelerated the brief.**
`project-model-trainer-role.md` captured the right design learnings (prerequisite sequence, MPS constraints, callback-based logging, checkpoint cleanup). The brief and architect drew on this directly. This is the memory system working as intended — no re-derivation from first principles.

---

## What Could Have Gone Better

**Architect output initially contained Jigsaw-specific content.**
The first architect output included a Per-Category Accuracy table with Jigsaw label columns and assumed a zero-shot baseline exists. The human caught this during review and required a rewrite. Root cause: the architect role was designing from the context of project 8 rather than from the brief's stated generality requirement. The brief explicitly said "generic enough to be reused across model architectures" — this should have been the architect's primary constraint, not a secondary consideration.

**Language conventions loaded unnecessarily for a Markdown deliverable.**
The planner, architect, and implementer all loaded `python-conventions.md` per the routing.md convention. None referenced it in their outputs — the deliverable is a Markdown file with no Python code. This is structural: `new-project-full` was designed for software projects. Using it for a workspace role definition caused three unnecessary resource loads.

**Architect specified step 1.3 without a concrete check method.**
"Confirm `<dataset_env_var>` in `.env` resolves to `dataset_path`" stated what to confirm but not how. The implementer faithfully reproduced this vagueness. The reviewer caught it. The root cause is in the architect output, not the implementer — the architect should specify validation steps precisely enough that the implementer doesn't need to interpret them.

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| Planner | `python-conventions.md` loaded; not referenced in output | Low | Skip for Markdown-only deliverables |
| Architect | `python-conventions.md` loaded; not referenced in output | Low | Skip for Markdown-only deliverables |
| Implementer | `python-conventions.md` + `vibecoding-style.md` loaded; neither referenced | Low–Medium | Skip for Markdown-only deliverables |
| Architect (pass 1) | Full rewrite required due to project-specific content; doubled architect context cost | Medium | Generalisation check before writing output |

### Redundancy Patterns

The architect's Open Questions Resolved section and the planner's Brief Flags Resolved section both restated the same four decisions. The architect section was necessary (it confirmed the decisions). The planner section was redundant — the planner made the decisions; the architect just confirmed them. The planner's "Brief Flags Resolved" section added context load without adding new information by the time the architect ran.

### Scoping Recommendations

- Planner should not write a "Flags Resolved" section — those resolutions belong in the architect output where they are confirmed, not the planner output where they are proposed.
- For a `new-role` sequence (see below), skip loading language conventions files at all roles. The deliverable is Markdown.

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| — | — | — | — |

### Skills to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| — | — | — | — |

### Routing Changes

| Sequence | Change | Reason | Human decision required? |
|----------|--------|--------|--------------------------|
| `new-project-full` | Add a note: when the deliverable is Markdown-only (e.g. a workspace role definition), planner/architect/implementer should not load language conventions files | Prevents unnecessary context load for non-code projects | No |
| `routing.md` | Add a `new-role` sequence (see below) | Dedicated lighter-weight sequence for workspace role creation | Yes — review the proposed sequence before adding |

### New Resources or Skills Needed

**Proposed: `new-role` sequence in `routing.md`**

```
## Sequence: `new-role`

Objective: Create a new reusable workspace role (CONTEXT.md + output template).
Use when: Adding a role that does not exist yet. Deliverable is Markdown only.
Review gate: After architect (confirm spec before writing the contract); after reviewer.

| Step | Role     | Reads                          | Resources              | Skills | Output                              |
|------|----------|-------------------------------|------------------------|--------|-------------------------------------|
| 1    | brief    | —                             | vibecoding-style.md    | —      | roles/brief/output/output.md        |
| 2    | planner  | brief/output.md               | vibecoding-style.md    | —      | roles/planner/output/output.md      |
| 3    | architect| planner/output.md             | —                      | —      | roles/architect/output/output.md    |
| 4    | implementer | architect/output.md        | vibecoding-style.md    | —      | roles/implementer/output/output.md  |
| 5    | reviewer | implementer/output.md + files | —                      | —      | roles/reviewer/output/output.md     |
| 6    | retro    | reviewer/output.md, implementer/output.md, project-state.md | vibecoding-style.md, routing.md | — | roles/retro/output/output.md |
```

No language conventions files loaded at any step. The architect note should include: "When designing a role, verify the contract would work unchanged on a project with a completely different dataset, label schema, and model architecture. If it would not, the contract is not generic enough."

**Proposed: Architect role note on generalisation**
Add to `roles/architect/CONTEXT.md` Notes section:
> When the deliverable is a workspace role (not software code), apply a generalisation check before writing output: would this role contract work unchanged on a project with a completely different dataset, task, and model family? If not, identify what is project-specific and convert it to an input field.

---

## One Change to Make Now

**Add the `new-role` sequence to `resources/routing.md`.**

This is the highest-value change because it prevents the two main friction points from this session recurring: unnecessary language conventions loading and absence of a generalisation prompt in the architect step. The sequence is short and well-defined above — it can be appended to routing.md as a new section immediately.

---

## Handoff

Human reviews recommendations above. Suggested actions before the next project:
1. Append `new-role` sequence to `resources/routing.md` (text above is ready to paste).
2. Add generalisation check note to `roles/architect/CONTEXT.md` Notes section.
3. Add language-conventions skip note to `new-project-full` in `routing.md`.
4. Update `_config/project-state.md` to record model-trainer role complete and retro actioned.
