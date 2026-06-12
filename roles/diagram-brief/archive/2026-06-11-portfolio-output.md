# diagram-brief Output

## Diagram Title
Three-Project System Flow

## Target Document
**File:** `PORTFOLIO.md`
**Section:** How They Compose
**Placement:** before section body

## Audience
**Tier:** 2/3
**Persona:** A tech lead or hiring manager who has read the project descriptions and wants to see at a glance how the three systems connect before reading the prose explanation.

## Diagram Type
**Type:** Flowchart / Directed Graph
**Syntax:** Mermaid flowchart LR

## Must Show
1. Node "Red-Team Platform" — generates jailbreak attack traffic against a language model
2. Node "Safety Monitor" — classifies interactions using three classifiers, routes flagged events
3. Edge: Red-Team Platform → Safety Monitor, labeled "attack results"
4. Node "Review Dashboard" — surfaces flagged interactions for human review (part of the Safety Monitor project)
5. Edge: Safety Monitor → Review Dashboard, labeled "flagged interactions"
6. Node "Human + AI Reviewer" — the human review step at the end of the pipeline
7. Edge: Review Dashboard → Human + AI Reviewer (unlabeled — the reviewer works the queue)
8. Node "Error Hide-and-Seek" — measures the effectiveness of AI hints at the human review step
9. Dashed edge: Error Hide-and-Seek -.-> Human + AI Reviewer, labeled "measures AI-hint uplift"

## Must Not Show
- Kafka topic as a named component (too technical for Tier 2/3)
- PostgreSQL or database nodes
- API endpoint paths
- The three individual classifier names (Pair, Prompt, Taxonomy)
- Escalation router internals or the 2x2 priority matrix
- Individual model names (DeBERTa, RoBERTa)
- Red-team clustering or corpus details

## Label Style
human-readable

## Layout
**Direction:** LR
**Grouping:** No subgraphs. Five nodes in a left-to-right pipeline, with Error Hide-and-Seek positioned below the pipeline connecting to Human + AI Reviewer via a dashed arrow.

## Handoff
The dashed arrow from Error Hide-and-Seek to Human + AI Reviewer represents measurement/validation, not a data flow — use `-.->` Mermaid syntax. The main pipeline (Red-Team Platform → Safety Monitor → Review Dashboard → Human + AI Reviewer) should read cleanly left-to-right; Error Hide-and-Seek is an annotation layer that sits outside the main flow.
