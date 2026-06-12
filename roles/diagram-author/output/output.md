# diagram-author Output

## Diagram Produced
Classification and Escalation Pipeline
`projects/llm-safety-monitor/README.md` — `## Architecture` section, before section body
Flowchart / Directed Graph — Mermaid flowchart LR

## Must Show Coverage
| Item | Status |
|------|--------|
| `kafka[Kafka Topic]` — event source node | Drawn |
| Subgraph `cls[Classifiers]` containing pair, prompt, taxonomy consumer nodes | Drawn |
| Three edges: kafka → pair, kafka → prompt, kafka → taxonomy | Drawn |
| `db[(classifications — PostgreSQL)]` — database node | Drawn |
| Three edges: pair → db, prompt → db, taxonomy → db | Drawn |
| `poller[Escalation Poller]` | Drawn |
| Edge: db → poller | Drawn |
| `queue([Review Queue])` — high-severity terminal | Drawn |
| Edge: poller → queue labeled "JAILBREAK / BENIGN_HARMFUL / MODEL_DISAGREEMENT" | Drawn |
| `logged([Mark escalated])` — log-only terminal | Drawn |
| Edge: poller → logged labeled "LOG_ONLY / None" | Drawn |

## Deviations from Brief
- Used `([Review Queue])` and `([Mark escalated])` stadium/pill shape (instead of plain rectangle) to visually distinguish the two terminal nodes as external outcomes rather than internal pipeline components. Consistent with Mermaid convention for external systems.
- Inserted `#### Classification and Escalation Pipeline` heading above the diagram block rather than no heading. The document uses `##` only; `####` skips a level but is the lowest heading the author CONTEXT.md permits. This gives the diagram a named anchor.

## Author Notes in Diagram
None.

## Handoff
The diagram-reviewer reads the diagram-brief and the embedded diagram.
Key concern: verify the edge label "JAILBREAK / BENIGN_HARMFUL / MODEL_DISAGREEMENT" renders legibly on GitHub — it is 44 characters and may need shortening if it crowds the layout.
