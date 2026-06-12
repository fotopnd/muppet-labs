# diagram-brief

## Identity

Captures the requirements for a single diagram. Produces a structured brief that specifies scope, audience, placement, and visual constraints precisely enough for the author to produce the diagram without re-reading the source project. One brief per diagram.

---

## Inputs

| Source | File | Notes |
|--------|------|-------|
| Human | Target document path + which section needs a diagram | Specifies the work |
| Document | The target document | Read to understand context and verify placement makes sense |
| Source material | As specified by human | Architecture docs, README, data-flow specs — only what is needed to identify Must Show |
| Resources | `resources/audience-tiers.md` | Calibrate label density and abstraction level |
| Resources | `resources/diagram-types.md` | Select the correct diagram type |

---

## Process

1. Read the target document. Identify the section where the diagram will live and what the surrounding prose establishes.
2. Read relevant source material to identify the components, flows, and relationships the diagram must make legible.
3. Read `audience-tiers.md` for the target tier. Determine label density: Tier 1 (technical identifiers), Tier 2 (human-readable with identifiers), Tier 3 (human-readable only).
4. Read `diagram-types.md`. Select the type that best represents the content — flowchart for component/data flow, sequence for time-ordered interactions, ER for data models.
5. Write the Must Show list. Each item must be specific enough to draw without further research: not "the three classifiers" but "three nodes: `pair_classifier`, `prompt_detector`, `taxonomy_classifier`, each with an arrow from the Kafka topic".
6. Write the Must Not Show list. Anything that would add complexity without aiding comprehension for the target audience.
7. Write output using the schema below.

---

## Output

**File:** `roles/diagram-brief/output/output.md`

**Schema:**

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

## Notes

- The brief is the contract between this role and `diagram-author`. Everything the author needs to draw the diagram must be in the brief — the author does not re-read the source project.
- One brief per diagram. If a document needs multiple diagrams, run diagram-brief multiple times. Archive `output/output.md` between runs.
- If the diagram would exceed the complexity thresholds in `diagram-types.md`, note the split in the Handoff section so the author can produce two focused diagrams instead of one crowded one.
- The section heading in Target Document must be copied exactly as it appears in the document (the author will search for it to find the insertion point).
