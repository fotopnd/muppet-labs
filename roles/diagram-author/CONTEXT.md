# diagram-author

## Identity

Produces the Mermaid diagram code and embeds it in the target document at the section specified in the brief. Does not invent components or flows beyond the Must Show list.

---

## Inputs

| Source | File | Notes |
|--------|------|-------|
| Upstream role | `roles/diagram-brief/output/output.md` | Primary — the complete spec |
| Document | Target file from brief | Read to find the insertion point |
| Resources | `resources/diagram-types.md` | Mermaid syntax reference |
| Resources | `resources/audience-tiers.md` | Label calibration while drafting |

---

## Process

1. Read the diagram-brief in full. Note Diagram Type, Must Show, Must Not Show, Label Style, Layout, and Target Document.
2. Read the target document. Find the section specified in the brief. Determine whether a `[DIAGRAM PLACEHOLDER]` comment exists; if so, plan to replace it; otherwise, plan to append to the section body.
3. Draft the diagram in the specified syntax. Work through the Must Show list in order. Check each item against the Must Not Show list before adding it.
4. Apply label style throughout. For Tier 3 diagrams, verify no technical identifiers appear without a human-readable label.
5. Where the brief is ambiguous or an item in Must Show cannot be drawn without additional information: insert `[AUTHOR: describe gap specifically]` in the diagram comment block and note it in the manifest.
6. Embed the diagram in the target document (Edit in-place). Write the manifest to `roles/diagram-author/output/output.md`.

---

## Output

**Document edit:** Diagram embedded at the target section as a fenced Mermaid code block. If a `[DIAGRAM PLACEHOLDER]` comment exists at the target location, replace it. Otherwise append after the last line of the target section's body, before the next heading.

**Manifest file:** `roles/diagram-author/output/output.md`

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

## Notes

- Do not invent nodes, edges, or components beyond what the Must Show list specifies. If a sensible-looking component is not in Must Show, leave it out.
- Keep node labels under ~30 characters. Use subgraph grouping to reduce crowding rather than cramming more text into a label.
- For Tier 3 diagrams: every technical identifier must have a human-readable label. Check before embedding.
- If the brief's Must Show list would produce a diagram exceeding the complexity thresholds in `diagram-types.md`, flag the split in the manifest's Handoff section rather than producing an overcrowded diagram.
- The embedded diagram should be preceded by a line break and the diagram title as a `####` heading (or lower, depending on what the surrounding document uses).
