# Architect Output — diagram-workflow roles

**Role:** architect
**Sequence:** new-role

---

## System Overview

Four deliverables compose the diagram workflow: three role CONTEXT.md files (`diagram-brief`, `diagram-author`, `diagram-reviewer`) and one resource catalog (`diagram-types.md`). A fifth edit adds the `design-diagram` sequence to `routing.md`. The three roles follow the same brief → author → reviewer pattern as `write-doc`, with two review gates: after diagram-brief (confirm scope before drawing) and after diagram-reviewer (confirm correctness before the diagram is committed). No new files are created by the author — it edits the target document in-place.

---

## Open Questions — Resolved

**Multi-diagram briefs:** One brief per diagram. Confirmed. If a document needs three diagrams, run diagram-brief three times, archiving the output between runs. This keeps each brief unambiguous and the author's job scoped.

**Author inserts vs replaces:** The author inserts at the target section specified in the brief. If a `[DIAGRAM PLACEHOLDER]` comment exists in the document, it replaces that comment. Otherwise, it appends to the body of the specified section heading. The brief must specify the section heading exactly as it appears in the document.

**ASCII / fallback formats:** Out of scope. Mermaid is the default. The diagram-reviewer may recommend SVG as a fallback if a Mermaid diagram exceeds a legible complexity threshold, but SVG authoring is outside the role contract.

---

## diagram-brief CONTEXT.md Spec

**Identity:** Captures the requirements for a single diagram. Produces a structured brief that specifies scope, audience, placement, and visual constraints precisely enough for the author to produce the diagram without re-reading the source project.

**Inputs table:**
| Source | File | Notes |
|--------|------|-------|
| Human | Target document path + which section needs a diagram | Specifies the work |
| Document | The target document | Read to understand context and verify placement makes sense |
| Source material | As specified by human | Architecture docs, README, data-flow specs — only what is needed to identify Must Show |
| Resources | `resources/audience-tiers.md` | Calibrate label density and abstraction level |
| Resources | `resources/diagram-types.md` | Select the correct diagram type |

**Process (7 steps):**
1. Read the target document. Identify the section where the diagram will live and what the surrounding prose establishes.
2. Read relevant source material to identify the components, flows, and relationships the diagram must make legible.
3. Read `audience-tiers.md` for the target tier. Determine label density: Tier 1 (technical identifiers), Tier 2 (human-readable with identifiers), Tier 3 (human-readable only).
4. Read `diagram-types.md`. Select the type that best represents the content — flowchart for component/data flow, sequence for time-ordered interactions, ER for data models.
5. Write the Must Show list. Each item must be specific enough to draw without further research: not "the three classifiers" but "three nodes: `pair_classifier`, `prompt_detector`, `taxonomy_classifier`, each with an arrow from the Kafka topic".
6. Write the Must Not Show list. Anything that would add complexity without aiding comprehension for the target audience.
7. Write output using the schema below.

**Output file:** `roles/diagram-brief/output/output.md`

**Output schema (exact sections):**

```markdown
## Diagram Title
[short title, used as the heading above the diagram in the document]

## Target Document
**File:** [path]
**Section:** [exact section heading text as it appears in the document]
**Placement:** before section body | after first paragraph | replace [DIAGRAM PLACEHOLDER]

## Audience
**Tier:** [1 / 2 / 3]
**Persona:** [one sentence — who will read this diagram and what do they already know]

## Diagram Type
**Type:** [name from diagram-types.md]
**Syntax:** [Mermaid flowchart LR | Mermaid sequence | Mermaid erDiagram | etc.]

## Must Show
[Numbered list. Each item must be specific enough to draw without further research.]
1. [Node / component: name and brief description]
2. [Edge / flow: from X to Y, label, direction]
...

## Must Not Show
[Bulleted list of explicit exclusions]
- [item]

## Label Style
technical identifiers | human-readable | both (format: "Human Name (`tech_id`)")

## Layout
**Direction:** LR | TD | RL | BT
**Grouping:** [subgraph groupings if any — e.g. "group the three consumers in a subgraph labelled Classifiers"]

## Handoff
[One or two sentences: what the author should pay close attention to, and any known visual challenge]
```

---

## diagram-author CONTEXT.md Spec

**Identity:** Produces the Mermaid diagram code and embeds it in the target document at the section specified in the brief. Does not invent components or flows beyond the Must Show list.

**Inputs table:**
| Source | File | Notes |
|--------|------|-------|
| Upstream role | `roles/diagram-brief/output/output.md` | Primary — the complete spec |
| Document | Target file from brief | Read to find the insertion point |
| Resources | `resources/diagram-types.md` | Mermaid syntax reference |
| Resources | `resources/audience-tiers.md` | Label calibration while drafting |

**Process (6 steps):**
1. Read the diagram-brief in full. Note Diagram Type, Must Show, Must Not Show, Label Style, Layout, and Target Document.
2. Read the target document. Find the section specified in the brief. Determine whether a `[DIAGRAM PLACEHOLDER]` comment exists; if so, plan to replace it; otherwise, plan to append to the section body.
3. Draft the diagram in the specified syntax. Work through the Must Show list in order. Check each item against the Must Not Show list before adding it.
4. Apply label style throughout. For Tier 3 diagrams, verify no technical identifiers appear without a human-readable label.
5. Where the brief is ambiguous or an item in Must Show cannot be drawn without additional information: insert `[AUTHOR: describe gap specifically]` in the diagram comment block and note it in the manifest.
6. Embed the diagram in the target document (Edit in-place). Write the manifest to `roles/diagram-author/output/output.md`.

**Output — document edit:** Diagram embedded at the target section as a fenced Mermaid code block.

**Output — manifest file:** `roles/diagram-author/output/output.md`

**Manifest schema:**
```markdown
## Diagram Produced
[Diagram title]
[Target file and section]
[Diagram type and syntax used]

## Must Show Coverage
| Item | Status |
|------|--------|
| [item from brief] | Drawn / Not drawn (see Author Note) |

## Deviations from Brief
[Any departure from the brief's spec and why — or "None"]

## Author Notes in Diagram
[List any [AUTHOR: ...] markers left in the diagram block, and what information is needed]
[Or "None"]

## Handoff
The diagram-reviewer reads the diagram-brief and the embedded diagram.
Key concern: [one thing the reviewer should examine closely]
```

---

## diagram-reviewer CONTEXT.md Spec

**Identity:** Formal editor for diagrams. Reads the brief and the embedded diagram, edits the diagram in-place, and issues a READY or AUTHOR REWORK NEEDED verdict.

**Inputs table:**
| Source | File | Notes |
|--------|------|-------|
| Upstream role | `roles/diagram-brief/output/output.md` | The contract |
| Document | Target file from brief | Contains the embedded diagram to review |
| Resources | `resources/audience-tiers.md` | Legibility standard for the target tier |

**Process (7 steps):**
1. Read the diagram-brief in full. Note Must Show, Must Not Show, Label Style, Layout, and Audience Tier.
2. Read the embedded diagram in the target document.
3. Check each item in Must Show against the diagram.
4. Check that nothing from Must Not Show appears.
5. Check label style against the brief's specification. For Tier 3: no unexplained technical identifiers.
6. Check layout direction and grouping against the brief.
7. Edit the diagram in-place for fixable issues. Insert `[AUTHOR: ...]` markers for gaps that require source knowledge the reviewer does not have.

**Checks (enforced):**
- Every Must Show item is present and correctly labelled
- No Must Not Show items appear
- Label style matches brief
- Flow direction is consistent — no arrows that contradict the described data flow
- No node labels truncated (keep labels under ~30 characters; use subgraph grouping to reduce crowding)
- For Tier 3: no raw technical identifiers without a human-readable equivalent

**READY** when: all Must Show items present, no Must Not Show items, label style correct, no `[AUTHOR: ...]` gaps.

**AUTHOR REWORK NEEDED** when: one or more Must Show items cannot be drawn correctly without re-reading source material, or the diagram type is wrong for the content.

**Output file:** `roles/diagram-reviewer/output/output.md`

**Output schema:**
```markdown
## What Was Edited
[Specific changes made — e.g. "Relabelled pair_classifier node to match Tier 1 label style; added missing arrow from escalation router to case-queue; removed database node (Must Not Show)"]

## Author Flags
[List every [AUTHOR: ...] marker and what is needed — or "None"]

## Verdict
READY — diagram satisfies the brief and is publication quality.
or
AUTHOR REWORK NEEDED — [one sentence on the gap]

## Handoff
[If READY: "No further action required. Diagram is embedded at: [path]#[section]"]
[If AUTHOR REWORK NEEDED: "Author should address [AUTHOR: ...] flags, then diagram-reviewer does a second pass."]
```

---

## diagram-types.md Spec

A catalog resource with the following structure per type:

```markdown
### [Type Name]
| Field | Value |
|-------|-------|
| **Mermaid keyword** | [e.g. `flowchart LR`] |
| **Best for** | [what content this type conveys well] |
| **Not for** | [what to avoid using it for] |
| **Typical complexity** | low / medium / high |

**Minimal example:**
\`\`\`mermaid
[5–8 line example]
\`\`\`
```

Types to include: Flowchart/Directed Graph, Sequence Diagram, Entity-Relationship Diagram, State Diagram. (C4/component diagrams: note that Mermaid's `C4Context` is experimental; use `flowchart TD` with subgraphs as the stable alternative.)

---

## routing.md Addition Spec

Add after the `write-doc` sequence entry:

```markdown
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
```

---

## Generalisation Check

Each role contract was verified against a hypothetical completely different project (e.g. a Rust CLI tool with a PostgreSQL schema diagram):

- **diagram-brief:** All inputs are parameterised by what the human specifies (target document, source materials). Nothing assumes an LLM safety domain. ✓
- **diagram-author:** Reads from the brief, which is project-agnostic by construction. Mermaid syntax reference is domain-neutral. ✓
- **diagram-reviewer:** Checks are expressed against the brief's Must Show / Must Not Show lists, not against any hardcoded domain. ✓

All three contracts are fully generalisable.

---

## Implementation Notes for Implementer

- The four output/output.md blank templates should follow the schema defined above for each role. Write each as a short heading-only template (no filler text), so the first real run has a clear scaffold to overwrite.
- The routing.md edit should insert the `design-diagram` section immediately after the `write-doc` section, before the `daily-brief` section.
- Do not modify any existing role contracts.
- No language conventions files are needed — deliverables are Markdown only.

---

## Handoff

Next role: implementer (after human sign-off on this architect output)
The implementer creates the directory structure, writes the four CONTEXT.md files and blank output templates, and edits routing.md. Write in this order: `diagram-types.md` first (referenced by both brief and author), then `diagram-brief`, `diagram-author`, `diagram-reviewer`, then `routing.md`.
