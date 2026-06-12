# Retro — diagram-workflow roles

**Role:** retro
**Sequence:** `new-role`
**Date:** 2026-06-11

---

## Project

**Name:** diagram-workflow
**Sequence:** new-role
**Sessions:** 2 (brief + planner + architect in session 1; implementer + reviewer + retro in session 2, resumed after context compaction)
**Roles that ran:** brief → planner → architect (gate) → implementer → reviewer (PASS) → retro
**Outcome:** PASS — all 8 deliverables produced, no blocking issues

---

## What Went Well

**1 — Architect's resolved open questions became reliable ground rules**

The architect session closed three open questions (multi-diagram briefs, insert-vs-replace logic, ASCII fallback) with concrete decisions. Each decision propagated directly into the Notes sections of the relevant CONTEXT.md files. The implementer did not re-litigate any of them. When the brief specifies "one diagram per run" and the author contract says "replace `[DIAGRAM PLACEHOLDER]` if present, otherwise append," the author has no ambiguity. Tight architect outputs produce tight role contracts.

**2 — The diagram-brief output schema was defined before implementation began**

The architect specified all 9 sections of the brief output schema (Diagram Title, Target Document, Audience, Diagram Type, Must Show, Must Not Show, Label Style, Layout, Handoff) and the exact purpose of each. This is the most critical interface in the whole workflow — the contract between brief and author. Having it specified in full before the implementer ran meant the CONTEXT.md, the blank template, and the routing.md entry all referenced the same schema with no drift.

**3 — `diagram-types.md` was written first, referenced cleanly by both roles**

The implementer followed the architect's "write `diagram-types.md` first" order. Both `diagram-brief` and `diagram-author` CONTEXT.md files load it; neither had to duplicate type definitions. The resource is self-contained: type name, Mermaid keyword, best-for/not-for, complexity thresholds, minimal example.

---

## What Could Have Gone Better

**1 — Minor inconsistency in Flowchart complexity threshold**

`diagram-types.md` states "up to ~12 nodes before legibility degrades" in the per-type table, but the Complexity Thresholds section at the bottom sets soft limit 10 and hard limit 15 for Flowcharts. The reviewer noted this (W1). The Complexity Thresholds table is the authoritative reference (it is what the `diagram-brief` Notes section points to), but the type table's "~12 nodes" creates a slight contradiction for someone reading the type entry in isolation. Could have been caught by proofing the catalog end-to-end before writing the CONTEXT.md files that depend on it.

**2 — Blank templates are heading-only, which may feel sparse**

The blank `output/output.md` files contain only section headings with no placeholder text. Other role templates in the workspace (e.g. `doc-brief`) also follow this pattern, so this is consistent. But for a first-time user of `diagram-brief`, seeing a blank schema with no worked example or prompt text could be disorienting. An in-template comment like `[e.g. "Kafka Event Flow"]` in the Diagram Title slot would reduce first-run friction with no downside.

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| Implementer | Read all prior role outputs (brief, planner, architect) before writing — correct behavior, not waste | None | No change |
| Reviewer | Loaded all three CONTEXT.md files plus architect spec to check correctness | Low | Correct scope — reviewer's job is exactly this comparison |

### Redundancy Patterns

None identified. The role contracts do not duplicate content from `diagram-types.md` — they reference it by filename. The output schemas appear in the CONTEXT.md files once each (not in both CONTEXT.md and a separate template file).

### Scoping Recommendations

The `new-role` sequence loaded `_config/project-state.md` in the retro stage. For a Markdown-only workspace tooling project like this, `project-state.md` is lightly relevant (contains general workspace state but no diagram-workflow-specific history). This is acceptable for retro — the file is short and provides orientation.

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `resources/diagram-types.md` | In the Flowchart type table, change "up to ~12 nodes before legibility degrades" → "up to 10 nodes (soft limit); see Complexity Thresholds section below for hard limits" | Resolves the W1 inconsistency between the type entry and the Complexity Thresholds table | No |

### Skills to Update

None.

### Routing Changes

None. The `design-diagram` entry in `routing.md` was written correctly in this session. No structural changes needed.

### New Resources or Skills Needed

None identified. The three existing resources loaded by the diagram workflow (`audience-tiers.md`, `diagram-types.md`, `writing-voice.md` indirectly via audience-tiers) are sufficient.

---

## One Change to Make Now

**Fix the Flowchart complexity threshold inconsistency in `resources/diagram-types.md`.**

In the Flowchart type table, line:
> `Typical complexity | Low to medium — up to ~12 nodes before legibility degrades`

Change to:
> `Typical complexity | Low to medium — soft limit 10 nodes; see Complexity Thresholds section`

This closes the W1 finding from the reviewer, removes ambiguity for the first person who uses `diagram-brief` to brief a flowchart, and takes under 30 seconds to apply.

---

## Handoff

Human reviews recommendations above. Only one change recommended:

1. **Apply now (no decision required):**
   - Fix Flowchart complexity line in `resources/diagram-types.md` (one-line edit)

2. Update `_config/project-state.md` to record diagram-workflow retro complete and `design-diagram` sequence now available.

The `design-diagram` sequence is ready for first use. Candidate diagrams from `resources/priorities.md` P3:
- Three-project system flow → `PORTFOLIO.md`
- Kafka event → classifier → escalation pipeline → `projects/llm-safety-monitor/README.md`
- POST /sessions → annotate → score pipeline → `projects/error-hide-seek/README.md`
