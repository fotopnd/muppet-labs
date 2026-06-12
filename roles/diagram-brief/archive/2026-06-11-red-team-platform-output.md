# diagram-brief Output

## Diagram Title
Attack Pipeline and Outbox Integration

## Target Document
**File:** `projects/red-team-platform/README.md`
**Section:** Architecture
**Placement:** before section body

## Audience
**Tier:** 1
**Persona:** A software engineer reading the deep-dive who wants to see how the four components connect — especially how the transactional outbox bridges the attack runner and the safety monitor — before reading the prose.

## Diagram Type
**Type:** Flowchart / Directed Graph
**Syntax:** Mermaid flowchart LR

## Must Show
1. Node `corpus[(attacks corpus)]` — the seeded corpus table; attack runner reads from this
2. Node `runner[Attack Runner]` — reads attacks, sends to target LLM, calls pair classifier inline, writes results
3. Node `ollama([Target LLM])` — external system; use stadium shape to distinguish from internal components; edge from runner to ollama labeled "attack", return edge from ollama to runner labeled "response"
4. Subgraph labeled "PostgreSQL — same transaction" containing two nodes: `runs[(runs)]` and `outbox[(outbox)]`; both written by the runner in the same DB transaction
5. Edges from runner → runs and runner → outbox (both pointing into the subgraph, representing the single transaction write)
6. Node `publisher[Outbox Publisher]` — separate daemon; polls outbox table
7. Edge from outbox → publisher labeled "poll unpublished"
8. Edge from publisher → kafka node
9. Node `kafka([Kafka Topic])` — use stadium shape; output channel to the monitor
10. Edge from kafka → monitor node labeled "LLMInteractionEvent"
11. Node `monitor([Safety Monitor])` — downstream consumer; stadium shape
12. Node `cluster[cluster CLI]` — post-sweep clustering step; reads from runs table
13. Edge from runs → cluster labeled "post-sweep"
14. Node `fclusters[(failure_clusters)]` — cluster output written by the CLI

## Must Not Show
- React dashboard (read-only consumer of stored data; not part of the write pipeline)
- Alembic migrations
- TF-IDF / KMeans internals
- `FOR UPDATE SKIP LOCKED` implementation detail (explain in prose, not diagram)
- Pair classifier as a separate node — it is called inline by the runner; showing it separately overstates its independence from the runner process
- Harm category labels or cluster names from Phase 1 results

## Label Style
technical identifiers

## Layout
**Direction:** LR
**Grouping:** Subgraph "PostgreSQL — same transaction" groups `runs` and `outbox` to make the transactional write visually explicit. This is the diagram's key architectural claim.

## Handoff
The subgraph label "PostgreSQL — same transaction" carries the transactional outbox design decision directly on the diagram — the author should not simplify it to just "PostgreSQL". The two outgoing paths from PostgreSQL (outbox → publisher → kafka, and runs → cluster → failure_clusters) form a fork; the LR direction should make this fork read naturally rather than stacking the two paths confusingly.
