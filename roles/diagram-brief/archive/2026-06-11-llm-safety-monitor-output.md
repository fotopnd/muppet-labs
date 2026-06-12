# diagram-brief Output

## Diagram Title
Classification and Escalation Pipeline

## Target Document
**File:** `projects/llm-safety-monitor/README.md`
**Section:** Architecture
**Placement:** before section body

## Audience
**Tier:** 1
**Persona:** A software engineer or ML practitioner reading the deep-dive to understand how the pipeline is structured before working through the prose detail.

## Diagram Type
**Type:** Flowchart / Directed Graph
**Syntax:** Mermaid flowchart LR

## Must Show
1. Node `kafka_topic`: labeled "Kafka Topic" — the event source; events are `LLMInteractionEvent` JSON payloads
2. Subgraph labeled "Classifiers" containing three nodes: `pair_consumer` ("Pair Consumer"), `prompt_consumer` ("Prompt Consumer"), `taxonomy_consumer` ("Taxonomy Consumer")
3. Edges from `kafka_topic` → each of the three consumer nodes (three parallel arrows)
4. Node `classifications_db`: labeled "classifications (PostgreSQL)" — use database node shape `[(label)]`
5. Edges from each of the three consumer nodes → `classifications_db` (three arrows converging)
6. Node `escalation_poller`: labeled "Escalation Poller" — reads when all 3 classification rows are present
7. Edge from `classifications_db` → `escalation_poller`
8. Node `review_queue`: labeled "Review Queue" — terminal for high-severity escalations; the monitor posts here but it is a downstream system, not part of the monitor's own pipeline
9. Edge from `escalation_poller` → `review_queue` labeled "JAILBREAK / BENIGN_HARMFUL / MODEL_DISAGREEMENT"
10. Node `log_only`: labeled "Mark escalated" — terminal node for low-severity outcomes
11. Edge from `escalation_poller` → `log_only` labeled "LOG_ONLY / None"

## Must Not Show
- FastAPI application and its REST endpoints
- React dashboard
- DeBERTa model loading or inference internals
- Kafka consumer group configuration details
- Red-team platform as a source (it publishes to the same Kafka topic, but it is out of scope for this diagram's story)
- `compute_escalation_reason` function internals or the 2x2 escalation matrix
- Bimodal calibration details
- Case-queue API by name — the downstream review system is out of scope; "Review Queue" is sufficient

## Label Style
technical identifiers

## Layout
**Direction:** LR
**Grouping:** Group the three consumer nodes (`pair_consumer`, `prompt_consumer`, `taxonomy_consumer`) in a subgraph labeled "Classifiers". This clusters the parallel processing tier visually and signals that the three consumers operate independently on the same input.

## Handoff
The three converging arrows (one per consumer → `classifications_db`) are the visual representation of the "poller waits for all three" invariant — the author should make sure all three arrows land on the same database node rather than three separate nodes. The split after the escalation poller (two outgoing edges with different labels) must clearly differentiate the case-creating path from the log-only path.
