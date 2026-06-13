# Brief Output — diagram-workflow roles

**Role:** brief
**Sequence:** new-role
**Mode:** structured (portfolio-quality workspace tooling)

---

## Project Name

`diagram-workflow` — three reusable workspace roles for designing and reviewing architecture diagrams and flow visualizations

## Description

Three roles (`diagram-brief`, `diagram-author`, `diagram-reviewer`) that together form a `design-diagram` routing sequence, enabling any project document to receive a reviewed, audience-calibrated diagram using the same brief → author → reviewer pattern as `write-doc`.

## Language(s)

Markdown only. No source code. Deliverables are `CONTEXT.md` role contracts and blank `output/output.md` templates.

## Success Criteria

- `roles/diagram-brief/CONTEXT.md` — complete role contract that a future session can execute without additional context
- `roles/diagram-author/CONTEXT.md` — complete role contract covering diagram type selection, Mermaid authoring, and document embedding
- `roles/diagram-reviewer/CONTEXT.md` — complete role contract covering correctness checks, legibility assessment, and READY/REWORK verdict
- `resources/diagram-types.md` — catalog of diagram types and when to use each (Mermaid flowchart, sequence, component, etc.), analogous to `doc-types.md`
- `resources/routing.md` updated with a `design-diagram` sequence entry
- All four `output/output.md` files are blank templates ready for first use

## Constraints

- Roles must be generalisable: the contracts must work on any project in the workspace, not just the portfolio projects that motivated them
- Mermaid is the default rendering target because it renders natively on GitHub without static assets
- Role contracts must follow the same structural conventions as existing roles (Identity, Inputs table, Process, Output, Notes sections)
- The `diagram-brief` role must support a one-diagram-per-document use case and a multi-diagram-per-document use case

## Out of Scope

- Generating any actual diagrams (that is the work the new roles will do in future sessions)
- Modifying any existing role contracts
- Creating a diagram template file (the diagram-brief role defines structure per diagram, not via a static template)

## Assumptions

- Mermaid is the preferred syntax because the portfolio will be published on GitHub and Mermaid renders in GitHub Markdown natively. The reviewer role should still support SVG as an alternative if a diagram is too complex for Mermaid.
- The `design-diagram` sequence has the same two review gates as `write-doc`: after diagram-brief (confirm scope before designing) and after diagram-reviewer (confirm correctness before committing to the document).
- The three roles are named `diagram-brief`, `diagram-author`, and `diagram-reviewer` to parallel the write-doc role names.

## Handoff

Next role: planner
The planner reads this file to define the exact contract for each role: what each role reads, what it produces, and what decisions it makes. Pay particular attention to the diagram-brief contract — it needs to capture enough information for the author to produce a diagram without re-reading the source project.
