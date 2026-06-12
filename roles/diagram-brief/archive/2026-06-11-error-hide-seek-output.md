# diagram-brief Output

## Diagram Title
Session Creation Pipeline

## Target Document
**File:** `projects/error-hide-seek/README.md`
**Section:** Architecture
**Placement:** after first paragraph

## Audience
**Tier:** 1
**Persona:** A software engineer reading the deep-dive who wants to see the branching logic inside POST /sessions before reading the implementation prose.

## Diagram Type
**Type:** Flowchart / Directed Graph
**Syntax:** Mermaid flowchart TD

## Must Show
1. Start node: `POST /sessions` — entry point, carries the condition parameter
2. Process node: "Create session_row, fetch planted_error" — initial DB write
3. Decision diamond: "condition?" — branches on unaided / human_agent / agent_only
4. Edge from decision → terminal: labeled "unaided" — short-circuit path that skips Claude
5. Process node: "Call Claude inline — annotate(altered_abstract)" — shared by human_agent and agent_only; the inline call is the key design decision
6. Process node: "Store AgentAnnotation rows"
7. Decision diamond: "agent_only?" — splits the auto-score path from the human review path
8. Edge from decision → terminal labeled "no (human_agent)" — session returned, human will POST /reviews later
9. Process node: "score_detections()" — auto-score; only fires for agent_only
10. Process node: "Mark session complete"
11. Terminal node: "Return SessionOut" — common exit point for all paths

## Must Not Show
- POST /reviews endpoint flow (separate endpoint)
- GET /results endpoint
- React frontend or Vite proxy
- Per-reviewer navigation logic in the SPA
- Database schema or column names
- Parse failure handling (PARSE_FAILED status) — implementation detail, not main flow

## Label Style
technical identifiers

## Layout
**Direction:** TD
**Grouping:** No subgraphs. Linear top-down flow with two decision diamonds producing the three condition branches. The unaided branch short-circuits early; the human_agent and agent_only branches share the Claude call before diverging at the second decision.

## Handoff
The key visual to preserve: the unaided path never touches Claude (short-circuit from first diamond straight to return), while human_agent and agent_only both pass through "Call Claude inline" before the second diamond splits them. This makes the design decision ("auto-annotation on session creation, not deferred") legible at a glance. The two "Return SessionOut" paths should converge on a single terminal node.
