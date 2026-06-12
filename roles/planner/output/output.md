# Planner Output — diagram-workflow roles

**Role:** planner
**Sequence:** new-role

---

## What We Are Building

Four Markdown files:
1. `roles/diagram-brief/CONTEXT.md`
2. `roles/diagram-author/CONTEXT.md`
3. `roles/diagram-reviewer/CONTEXT.md`
4. `resources/diagram-types.md`

Plus blank `output/output.md` templates under each role directory. The `routing.md` update is a fifth file edit.

---

## Role Contracts — Detailed Spec

### diagram-brief

**Purpose:** Define what a diagram must show before anyone starts drawing it. The output is a structured brief that fully specifies the diagram's scope, audience, rendering target, and visual constraints — enough for the author to produce the diagram without re-reading the source project.

**What it reads:**
- The document the diagram will be embedded in (to understand context and identify placement)
- The project's source material (architecture docs, README, results tables) as needed to understand what to show
- `resources/audience-tiers.md` — to calibrate label density and abstraction level for the target audience tier
- `resources/diagram-types.md` — to select the appropriate diagram type

**What it produces:** `roles/diagram-brief/output/output.md` with these sections:
- `Diagram Title` — the title that will appear above or in the diagram
- `Target Document` — exact file path and section heading where the diagram will be inserted
- `Audience Tier` — Tier 1 / Tier 2 / Tier 3, with persona note
- `Diagram Type` — type name from `diagram-types.md` and rendering syntax (Mermaid flowchart, sequence, etc.)
- `Must Show` — ordered list of components, flows, or relationships that must appear
- `Must Not Show` — explicit exclusions that keep the diagram focused
- `Label Style` — how components should be labelled (technical names, human-readable names, or both)
- `Layout Hint` — directional flow (top-down, left-right) and any layout constraints
- `Handoff` — what the diagram-author should pay attention to

**Key decision:** The brief must capture enough that the author can produce the diagram without reading the source document. Everything the author needs to know about what to draw is in the brief.

---

### diagram-author

**Purpose:** Produce the diagram code and embed it in the target document at the specified location.

**What it reads:**
- `roles/diagram-brief/output/output.md` — the complete spec
- The target document (to find the insertion point and verify placement makes sense in context)
- `resources/diagram-types.md` — syntax reference for the chosen type
- `resources/audience-tiers.md` — calibration while drafting labels

**What it produces:**
- The diagram embedded in the target document at the section specified in the brief (edit in-place, not a new file)
- `roles/diagram-author/output/output.md` — a manifest with: diagram title, target file, diagram type used, any deviations from brief, and any `[AUTHOR: ...]` gaps

**Key decisions the author makes:**
- Exact node labels (must match the brief's label style)
- Layout (must match the brief's layout hint or note deviation)
- Whether to use a Mermaid subgraph to group related components
- Whether a complex diagram should be split into two simpler ones (flag in output.md if so)

**Constraint:** The author does not invent components or flows that are not in the brief's Must Show list. If the diagram requires something that is not in the brief, the author inserts `[AUTHOR: need spec for X]` and flags it in the manifest.

---

### diagram-reviewer

**Purpose:** Edit the embedded diagram in-place until it satisfies the brief and is legible at the target audience tier.

**What it reads:**
- `roles/diagram-brief/output/output.md` — the contract
- The document containing the embedded diagram
- `resources/audience-tiers.md` — legibility standard for the tier

**What it produces:**
- The diagram edited in-place (Mermaid code corrected, labels sharpened, layout adjusted)
- `roles/diagram-reviewer/output/output.md` — summary of changes + READY or AUTHOR REWORK NEEDED verdict

**Checks to perform:**
1. Every item in Must Show is present and correctly labelled
2. Nothing from Must Not Show appears
3. Label style matches the brief's specification
4. Flow direction is consistent (no arrows that contradict the data flow)
5. The diagram is legible at typical GitHub render width (no node labels truncated, no crowded subgraphs)
6. For Tier 3 diagrams: no unexplained technical acronyms in labels

**AUTHOR REWORK NEEDED** when: the Must Show list has a gap that cannot be filled without re-reading the source project, or the diagram type is wrong for the content (e.g. a flowchart was used where a sequence diagram is needed).

---

## diagram-types.md Spec

A catalog of available diagram types with: type name, rendering syntax, what it is best for, when not to use it, and a minimal Mermaid example. Types to include:

1. **Flowchart / directed graph** — component relationships, data flow, decision trees
2. **Sequence diagram** — time-ordered interactions between systems or actors
3. **Entity-relationship diagram** — database schemas, data model relationships
4. **Component / architecture diagram** — how subsystems connect (Mermaid's `graph` or `C4Context`)
5. **State diagram** — lifecycle of an entity through states

---

## routing.md Addition Spec

Add a `design-diagram` sequence entry with:
- Objective: Produce a reviewed, embedded diagram for a specific document and audience
- Use when: A document needs a diagram to convey architecture or flow that prose cannot efficiently cover
- Review gates: after diagram-brief (confirm scope); after diagram-reviewer (confirm correctness)
- Three steps: diagram-brief → diagram-author → diagram-reviewer
- Note: the sequence produces no new files; it edits an existing document in-place

---

## File Structure to Create

```
roles/
  diagram-brief/
    CONTEXT.md          ← role contract
    output/
      output.md         ← blank template
  diagram-author/
    CONTEXT.md
    output/
      output.md
  diagram-reviewer/
    CONTEXT.md
    output/
      output.md
resources/
  diagram-types.md      ← new catalog file
```

---

## Open Questions

**Q: Should diagram-brief support multi-diagram briefs (one output.md covers N diagrams for the same project)?**
Proposed answer: No. One brief per diagram. If a project needs three diagrams, run diagram-brief three times and produce three output.md files (archived after each). This keeps each brief focused and makes the author's job unambiguous.

**Q: Should diagram-author append diagrams to the document or replace existing ones?**
Proposed answer: Replace if a `[DIAGRAM: title]` placeholder exists, otherwise append to the specified section. The brief must specify the section heading clearly.

**Q: Should the reviewer role support ASCII art as a fallback for terminals / PDF renders?**
Proposed answer: No. ASCII diagrams are a separate concern. Mermaid is the default; SVG is the fallback for complex diagrams. ASCII is out of scope for this workflow.

---

## Handoff

Next role: architect
Confirm the role contracts as specified above. The architect should resolve the open questions and confirm the exact CONTEXT.md structure before implementation. Pay particular attention to the diagram-brief output schema — it is the contract between brief and author and must be precise enough that the author never needs to re-read the source project.
