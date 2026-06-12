# Implementer Output — diagram-workflow roles

**Role:** implementer
**Sequence:** new-role
**Project:** diagram-workflow

---

## Deliverables Produced

| File | Status | Notes |
|------|--------|-------|
| `resources/diagram-types.md` | Created | 4 types: Flowchart, Sequence, ER, State — with Mermaid keywords, best-for/not-for, complexity thresholds, minimal examples |
| `roles/diagram-brief/CONTEXT.md` | Created | Identity, Inputs table, 7-step Process, Output schema, Notes |
| `roles/diagram-brief/output/output.md` | Created | Blank template with all schema headings |
| `roles/diagram-author/CONTEXT.md` | Created | Identity, Inputs table, 6-step Process, Output (document edit + manifest), Notes |
| `roles/diagram-author/output/output.md` | Created | Blank manifest template |
| `roles/diagram-reviewer/CONTEXT.md` | Created | Identity, Inputs table, 7-step Process, Checks, Verdict conditions, Output schema, Notes |
| `roles/diagram-reviewer/output/output.md` | Created | Blank reviewer output template |
| `resources/routing.md` | Edited | Added `design-diagram` sequence after `write-doc`, before daily-brief section |

## Deviations from Architect Spec

None. All 8 deliverables produced in architect-specified order. All CONTEXT.md files follow Identity / Inputs / Process / Output / Notes structure as specified. All blank templates follow the schemas exactly.

---

## Handoff

Next role: reviewer

The reviewer reads the three CONTEXT.md files against the architect spec at `roles/architect/output/output.md` and issues READY or REWORK NEEDED for the role contracts as a set. Key concerns:
- diagram-brief output schema has all 9 sections (Title, Target Document, Audience, Diagram Type, Must Show, Must Not Show, Label Style, Layout, Handoff)
- diagram-author manifest schema matches architect spec
- diagram-reviewer output schema matches architect spec
- routing.md `design-diagram` section placed correctly (after `write-doc`, before daily-brief)
- All three CONTEXT.md Notes sections capture edge cases from architect's resolved open questions
