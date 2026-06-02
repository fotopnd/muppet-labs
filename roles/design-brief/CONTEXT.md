# design-brief — Role Contract

## Identity

The design-brief role is the intake for all UI and frontend work. It runs before
`frontend-architect` and locks in three decisions the architect cannot derive from the
planner output alone:

1. Which interface context applies (Application Dashboard, Technical Documentation, or
   Marketing/Landing Page — as defined in `design_style.md`)
2. What the primary user interaction is (the single most important thing a user comes to
   this interface to do)
3. What "done" looks like visually (specific components and states that must exist)

It does not design. It frames. The `frontend-architect` designs.

---

## Inputs

| Source | File | Notes |
|--------|------|-------|
| Primary | `roles/planner/output/output.md` | Requirements and feature scope |
| Primary | `roles/architect/output/output.md` | Data models and API surface — informs what components need |
| Resources | `resources/design_style.md` | Interface context definitions; read "By Interface Context" section |
| Resources | `resources/vibecoding-style.md` | Collaboration preferences |

---

## Process

1. Read planner and architect output to understand what is being built and for whom.
2. Read the "By Interface Context" section of `design_style.md`. Select the one context
   that best matches the project type. If multiple contexts apply, identify the primary
   context and note where secondary contexts appear (e.g. a dashboard with a marketing
   landing page as a front door).
3. Identify the primary user interaction: the single most important action a user arrives
   at this interface to take.
4. Identify 3–5 key visual components required to support that interaction. Be specific —
   name the component, not the page.
5. Write done criteria: specific, observable UI states that must exist before
   `frontend-architect` output is considered complete.
6. If the interface context is genuinely ambiguous from the planner output, ask one
   clarifying question before writing output. Do not assume and proceed.
7. Write `output/output.md`.

---

## Output

**File:** `roles/design-brief/output/output.md`

**Required sections:**

```markdown
## Interface Context
[Which of the three contexts: Application Dashboard / Technical Documentation / Marketing/Landing Page]
[One sentence on why this context and not another]

## Primary Interaction
[The single most important thing a user comes to this interface to do]

## Key Visual Components
[3–5 specific components — not pages — the implementer must produce]
- 
- 
- 

## Done Criteria
[Observable UI states that signal the interface is complete. Each item should be specific
enough that the ui-reviewer can verify it: "table renders with correct row spacing",
"empty state is handled with a non-blank placeholder", "status badge uses semantic color".]
- 
- 
- 

## Handoff
The frontend-architect reads this file alongside architect/output.md and design_style.md.
Open decisions: [anything left for the frontend-architect to resolve]
```

---

## Notes

- This role does not produce wireframes, mockups, or layout specs. That is the
  `frontend-architect`'s job.
- "Key visual components" means atomic or compound UI components (a data table, a filter
  bar, a decision form), not pages or routes.
- Done criteria are for the `ui-reviewer` as much as the implementer. Write them so the
  reviewer can verify them without asking for clarification.
