# Reviewer Output — red-team-platform dashboard refinement

**Role:** reviewer  
**Sequence:** existing-project-refinement (brief → planner → architect → implementer → reviewer)  
**Date:** 2026-06-13

---

## Summary

Full dashboard refinement pass across all 10 brief items. New backend endpoints (3), new frontend components (6), new hooks (3), revised pages (7), new utility libraries (2). One pre-output fix applied during this review pass (CoverageHeatmap legend swatches). No blocking issues. **PASS WITH NOTES**.

---

## Checklist vs Brief

| # | Issue | Addressed | How |
|---|-------|-----------|-----|
| 1 | Category names raw (LABEL_N) | ✓ | `categoryLabels.ts` with `labelName()`, `abbrevName()`, `categoryColour()` — no LABEL_N in rendered output (grep confirmed) |
| 2 | Attack browser needs topline widgets | ✓ | 3 × `StatWidget` cards: Total Attacks, Top Category, Top Strategy — backed by new `GET /attacks/summary` endpoint |
| 3 | Description box for category/strategy combo | ✓ | Row click opens detail panel with `STRATEGY_DESCRIPTIONS` and `CATEGORY_LABELS` rendered in a `<dl>` |
| 4 | Coverage heatmap larger/touching cells | ✓ | `CoverageGrid` CSS grid replaces Recharts ScatterChart; cells 62×48 px, no gaps, truncated labels, fixed-position tooltip |
| 5 | Strategy comparison better graphs | ✓ | 3-panel: ASR bar with `n=` annotation, horizontal volume bar (accent), compact `CoverageGrid` |
| 6 | Regression 2–4 charts | ✓ | 4-panel: ASR line with baseline `ReferenceLine`, category-delta bar (red/green `Cell`), session table, best/worst `StatWidget` pair |
| 7 | Sample review dedup | ✓ | Compare mode: 200-row ceiling, client-side group by `attack_text`, #Total/#Success/#Safe counts, side-by-side `RunCard` on click |
| 8 | Failure clusters bubble chart | ✓ | Recharts `ScatterChart` + `ZAxis` bubble chart above card grid; area ∝ failure count |
| 9 | Bias heatmap EN baseline column | ✓ | EN column rendered at `0.00` with `bg-divergence-low` class |
| 10 | Bias heatmap filterable + click-through viewer | ✓ | Government + topic filter dropdowns; click row opens inline `BiasResponseViewer` (3-column: EN / target lang / back-translated placeholder); Escape closes |

---

## Correctness

**C1 — Fixed (pre-output):** `CoverageHeatmap.tsx:43,46,49` — Three legend color swatches used `style={{ backgroundColor: 'hsl(120, 65%, 45%)' }}` (static literal values). All three replaced with Tailwind classes `bg-green-600`, `bg-yellow-600`, `bg-red-600` before this output was written.

**C2 — Note:** `BiasResponseViewer.tsx` — back-translation column is a placeholder ("Back-translation coming soon"). This is within brief scope (brief says "back-translated placeholder"). Fine as shipped.

**C3 — Note:** `SampleReview.tsx` Compare mode ceiling is 200 rows client-side. Per architect decision D7, this is intentional with a UI note. Acceptable — the attack corpus is static.

**C4 — Note:** `GET /regression/category-delta` uses a `text()` SQL query for the per-session ASR calculation. Unlike `/attacks/summary` (which hit the asyncpg NULL type inference issue and was rewritten as ORM), this query always receives a resolved, non-null `session_id`. The `text()` approach is safe here.

No logic errors. No unhandled nulls. No type-unsafe narrowing. No missing error paths.

---

## Style

All remaining `style={{}}` instances are justified:

| File | Line(s) | Justification |
|------|---------|---------------|
| `CoverageGrid.tsx` | 54–120 | Runtime props (`cw`, `ch`, `rowHeaderWidth`, `compact`) — not expressible as Tailwind |
| `CoverageGrid.tsx` | 83 | Computed `hsl(${120*(1-asr)}, 65%, 45%)` — dynamic colour |
| `CoverageGrid.tsx` | 120 | Tooltip `left/top` at mouse coordinates |
| `ScoreBar.tsx` | 18 | `width: ${score * 100}%` — dynamic percentage |
| `StrategyComparison.tsx` | 68 | `<LabelList>` SVG text — Tailwind doesn't reach SVG |
| `RegressionTracker.tsx` | 108 | Same — Recharts `LabelList` SVG |
| `FailureClusters.tsx` | 117 | `cursor: 'pointer'` on Recharts `<Scatter>` SVG element |
| `FailureClusters.tsx` | 156 | `width: ${pct}%` — dynamic percentage |

All other conventions clean:
- `import type` on every type-only import ✓
- No `any`, no `!` assertions ✓
- `verbatimModuleSyntax` respected ✓
- Category labels only rendered through `labelName()` / `abbrevName()` ✓
- `staleTime` set on all three new hooks (0, 30s, 60s per data volatility) ✓

---

## Backend

- `/attacks/summary` — ORM approach avoids asyncpg NULL type inference bug; 3 separate queries (count, top_category, top_strategy); route placed before paginated `GET /attacks` to avoid path conflict ✓
- `/regression/category-delta` — two-session SQL aggregation; early return when <2 sessions exist; `model_name` auto-resolved from baseline session ✓
- `/bias/responses/{topic_id}` — LEFT JOINs on `bias_responses` and `bias_divergence_scores`; model auto-resolved from most recent score when not specified ✓
- `schemas.py` — 5 new Pydantic models (`AttackSummaryOut`, `CategoryDeltaItem`, `CategoryDeltaOut`, `BiasLangDetail`, `BiasTopicResponseOut`) ✓
- Ruff I001 (import sort) and E501 (line length >100) both clean ✓

---

## Refactor Candidates

**R1 (low priority):** `CoverageGrid.tsx` `compact` prop changes font size between two static values (8 and 11). These could be Tailwind responsive variants if the breakpoint were known at build time, but `compact` is a runtime prop so `style={{}}` is unavoidable. No action needed.

**R2 (low priority):** `BiasResponseViewer.tsx` hardcodes `['zh', 'ru', 'ar']` tab order. If languages are ever data-driven this should come from the API response keys. Fine for the current dataset.

---

## Verdict

**PASS WITH NOTES**

One pre-output fix applied (C1). All 10 brief items addressed. No blocking issues. Ready for retro and commit.

---

## Handoff

**Next role:** retro  
Read this output alongside `implementer/output/output.md` and `_config/project-state.md`. Extract workspace-level learnings (asyncpg NULL issue, CoverageGrid pattern, `text()` vs ORM decision rule) into resources. Then update `project-state.md` and commit all new/modified files.
