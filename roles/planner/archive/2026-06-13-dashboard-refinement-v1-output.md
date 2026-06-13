# Planner Output — Red-Team Platform Dashboard Refinement

**Role:** planner  
**Date:** 2026-06-13  
**Input brief:** `roles/brief/archive/2026-06-13-dashboard-refinement-brief.md`

---

## Project

red-team-platform-dashboard-refinement — a full UX and information-density pass over all seven dashboard tabs: fix LABEL_x category names, add topline insight widgets, replace ScatterChart-faked grids with CSS grids, migrate all inline styles to Tailwind tokens, add three new backend endpoints, and build a three-column bias response viewer.

---

## Requirements

### Shared / cross-cutting

1. A `web/src/lib/categoryLabels.ts` module exports `labelName(raw: string): string` mapping `LABEL_0`–`LABEL_12` to human names; unmapped values pass through unchanged.
2. A `web/src/lib/strategyDescriptions.ts` module exports `STRATEGY_DESCRIPTIONS` covering all six corpus strategies with `{ label, description, example }` per entry.
3. No `style={{…}}` prop appears in any tab or shared component file after implementation.
4. All colour, spacing, and typography references use `@theme` Tailwind tokens (`bg-canvas`, `text-text-primary`, `bg-surface-muted`, `border-border`, `text-accent`, `bg-accent-subtle`, `bg-divergence-*`).

### Backend

5. `GET /attacks/summary?source=&harm_category=&strategy=` returns `{ total, top_category, top_strategy }` computed over all attacks matching the filters (not just the current page).
6. `GET /regression/category-delta?model=` returns `[{ harm_category, baseline_asr, latest_asr, delta }]`; baseline = first RunSession for model, latest = most recent; returns empty array when fewer than two sessions exist.
7. `GET /bias/responses/{topic_id}?model=` returns `{ topic_id, government, label, languages: { [lang]: { prompt, response, cosine_distance } } }`; `model` defaults to most recently scored model; languages present only when a BiasResponse exists.

### Attack Browser

8. Three `StatWidget` cards render above the filter bar: total attacks, top harm category (human-readable), top strategy; cards update reactively when filters change.
9. Clicking a table row opens a right-side detail panel (≥ 40 % of page width); panel shows: full attack text, a `<dl>` strategy + category context box, and (if a run record exists) response text with `ScoreBar` and jailbreak badge.
10. Panel can be dismissed; row click does not navigate.

### Coverage Heatmap

11. The Recharts `ScatterChart` is replaced by the shared `CoverageGrid` component — cells touch (no gap), each cell renders its ASR% in readable text without hover.
12. Cells with no data show a neutral surface background with `"—"`.
13. Category row labels use `labelName()` and are fully readable; not rotated.
14. Hover tooltip shows full category name, strategy, run count, success count.

### Strategy Comparison

15. Three panels in a `grid grid-cols-1 lg:grid-cols-3` layout:
    - A: ASR % bar chart sorted descending, with `n=` run-count label on each bar.
    - B: horizontal bar chart of `total_runs` per strategy, using accent-purple colour.
    - C: compact `CoverageGrid` (~35×30 px cells) showing strategy × category coverage gaps.

### Regression Tracker

16. Four panels in a `grid grid-cols-1 lg:grid-cols-2` layout:
    - A: ASR-over-sessions line chart; first session's ASR shown as dashed baseline.
    - B: per-category delta bar chart from `/regression/category-delta` (red = regression, green = improvement); renders an explanatory empty state when fewer than 2 sessions exist.
    - C: session summary table (date, model, total runs, ASR, Δ vs previous) sortable by date.
    - D: two stat boxes: most-improved category and most-regressed category vs latest session.

### Sample Review

17. A mode toggle (All / Compare) renders above the run table; Compare is the default.
18. In Compare mode, runs are grouped by `attack_text` client-side; one row per unique attack shows `#Success`, `#Safe`, `#Total` columns; Compare mode fetches up to 200 runs per session.
19. Clicking a grouped row opens a two-column side panel: best-scoring run (left) vs lowest-scoring run (right); if all runs share an outcome, show only the highest scorer with a note.

### Failure Clusters

20. A Recharts `ScatterChart` bubble chart renders above the card grid; X = cluster index, Y = `size` (failure count), bubble radius ∝ `sqrt(size)`, colour = `top_harm_category` (categorical palette).
21. Clicking a bubble scrolls to and highlights the corresponding cluster card.
22. Each card includes a horizontal proportion bar showing this cluster's share of total failures.
23. All card `style={{}}` replaced with Tailwind utilities.

### Bias Heatmap

24. An `EN` column renders as `0.00` with `bg-divergence-low`; a footnote below the table reads "EN = 0.00 baseline; all values measure divergence from the EN response."
25. A government `<select>` and topic text `<input>` filter rows client-side; both controls appear above the table.
26. Clicking a topic row expands a response viewer panel below the table.
27. The response viewer shows three columns: EN (prompt + response), target language (prompt + response), back-translated (static placeholder `[Back-translation not yet available]`).
28. A ZH / RU / AR language selector switches columns 2 and 3.
29. A `useBiasResponses(topicId: string | null)` hook fetches `/bias/responses/{topic_id}` only when `topicId` is non-null.

---

## Technology Stack

| Concern | Choice | Reason |
|---|---|---|
| Frontend language | TypeScript 5.x strict | existing project |
| Framework | React 18 functional | existing project |
| Build | Vite + `@tailwindcss/vite` | existing project, port 5173 |
| Styling | Tailwind v4 `@theme` tokens | existing; mandatory migration for all tabs |
| Charts | Recharts | existing; retain for bar/line/bubble; replace ScatterChart-as-grid with CSS grid |
| Server state | TanStack Query | existing project |
| Backend language | Python 3.12 | existing project |
| API framework | FastAPI | existing project |
| DB access | SQLAlchemy async + asyncpg | existing project |
| Linting | ruff | existing project |
| FE testing | vitest + @testing-library/react | existing project |
| BE testing | pytest + pytest-asyncio | existing project |

---

## File and Module Structure

### New frontend files

```
web/src/lib/
  categoryLabels.ts           — LABEL_x → human name map + labelName() helper
  strategyDescriptions.ts     — strategy key → {label, description, example}

web/src/components/
  StatWidget.tsx              — metric card: icon + label + large value
  ScoreBar.tsx                — continuous 0–1 classifier score as a filled bar
  CoverageGrid.tsx            — reusable CSS grid heatmap; props: cells[], row/col labels, optional cellW/cellH

web/src/hooks/
  useAttackSummary.ts         — GET /attacks/summary with filter params
  useCategoryDelta.ts         — GET /regression/category-delta?model=
  useBiasResponses.ts         — GET /bias/responses/{topic_id}?model=
```

### Modified frontend files

```
web/src/pages/AttackBrowser.tsx       — stat widgets, row detail panel, style migration
web/src/pages/CoverageHeatmap.tsx     — replace ScatterChart with CoverageGrid, style migration
web/src/pages/StrategyComparison.tsx  — 3-panel layout using CoverageGrid for panel C
web/src/pages/RegressionTracker.tsx   — 4-panel layout, category delta + session table
web/src/pages/SampleReview.tsx        — Compare mode, dedup grouping, 2-col detail panel
web/src/pages/FailureClusters.tsx     — bubble chart, proportion bars, style migration
web/src/pages/BiasHeatmap.tsx         — EN column, filters, response viewer
```

### New backend files

None — all changes go into existing routers.

### Modified backend files

```
src/red_team_platform/api/routers/attacks.py     — add GET /attacks/summary
src/red_team_platform/api/routers/regression.py  — add GET /regression/category-delta
src/red_team_platform/api/routers/bias.py        — add GET /bias/responses/{topic_id}
src/red_team_platform/api/schemas.py             — add AttackSummaryOut, CategoryDeltaItem,
                                                     CategoryDeltaOut, BiasLangDetail,
                                                     BiasTopicResponseOut
```

---

## Open Questions for Architect

1. **`/regression/category-delta` query.** Computing per-category ASR requires grouping `Run.jailbreak_success` by `Attack.harm_category` within a session. The simplest form is two subqueries (one for the first session, one for the latest) then a Python-side merge. Confirm this approach or propose a SQL-level pivot.

2. **SampleReview dedup ceiling.** Compare mode fetches 200 runs per session. With 1,797 attacks and typically one run per attack per session, 200 rows covers ~11% of a full session. Decide: accept this limitation (display a "Showing first 200 — use filters to narrow" note), or add `GET /runs/grouped?session_id=` for server-side dedup.

3. **CoverageGrid compact labels.** Post-mapping category names are 20–35 chars. In the ~35×30 px compact cells used by StrategyComparison panel C, full names won't fit. Decide: truncate column headers to ~10 chars + tooltip, or rotate headers, or use an abbreviated version in a second mapping.

4. **Bubble chart categorical colour palette.** `top_harm_category` spans up to 13 LABEL values. Recharts ships 8 default colours. Decide: define a 13-colour palette in `categoryLabels.ts` alongside the label map (preferable), or cap at 8 with an "Other" bucket.

5. **`/attacks/summary` top_category/top_strategy computation.** MODE over all matching attacks requires a `GROUP BY + ORDER BY count DESC LIMIT 1` subquery. Two subqueries (one per field) is clean; a single CTE is more efficient. Confirm which.

---

## Handoff

Next role: architect  
The architect must resolve all five open questions and produce: (1) exact SQL or ORM query for `/regression/category-delta`; (2) decision on server vs client SampleReview dedup; (3) CoverageGrid abbreviated label strategy; (4) 13-colour palette definition; (5) `/attacks/summary` query pattern. The implementer works tab-by-tab, migrating inline styles as part of each tab's feature work — not as a separate pass.
