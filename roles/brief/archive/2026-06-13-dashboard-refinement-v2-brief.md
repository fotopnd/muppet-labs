# Brief — red-team-platform dashboard refinement v2

**Role:** brief  
**Sequence:** add-feature (existing-project refinement)  
**Date:** 2026-06-13  
**Project:** `projects/red-team-platform/web/`

---

## Problem Statement

Second refinement pass on the red-team-platform dashboard. Ten issues were addressed in v1; this pass addresses eleven new issues identified through review. The central themes are: tab consolidation (remove redundancy), richer analytical context (summary writeups), better visualisation (cluster axes, strategy colour, attack text formatting), a dedup fix in sample review, and live back-translation in the bias viewer.

---

## Issues (11)

| # | Issue | Component | Type |
|---|-------|-----------|------|
| 1 | Strategy taxonomy needs to be more descriptive | `strategyDescriptions.ts`, `AttackBrowser` | Content + display |
| 2 | Attack text formatting poor for readability | `AttackBrowser` detail panel | Display |
| 3 | Coverage heatmap tab is redundant | `App.tsx` nav | Nav removal |
| 4 | Strategy comparison ASR metrics are polarised (all red) | `StrategyComparison` | Chart colour |
| 5 | Strategy comparison needs a summary writeup of findings | `StrategyComparison` | New component |
| 6 | Regression tracker needs a summary writeup | `RegressionTracker` | New component |
| 7 | Regression tracker + strategy comparison should be one tab | `App.tsx`, new `Analytics.tsx` | Nav merge |
| 8 | Sample review returns duplicate attack text groups | `SampleReview`, `GET /runs` | Bug fix |
| 9 | Failure cluster graph not informative — X and Y redundant | `FailureClusters` bubble chart | Chart redesign |
| 10 | Cluster cards should be sorted by % of all failures | `FailureClusters` card grid | Sort order |
| 11 | Bias heatmap needs real back-translation for ZH/RU/AR | `BiasResponseViewer`, backend | New feature |

---

## Issue Details

### #1 — Strategy taxonomy more descriptive
`STRATEGY_DESCRIPTIONS` in `strategyDescriptions.ts` has 6 entries with brief (~1-sentence) descriptions. Issues:
- The corpus may contain strategy keys not in the current 6, causing raw key names to render.
- The `example` field is not rendered anywhere in the UI.
- Descriptions don't explain the mechanism, why it works, or what distinguishes it from others.

Fix: audit all strategy keys in the DB, expand each description to 2–3 sentences (mechanism + why it bypasses alignment + what to look for in responses), and render the `example` field in the AttackBrowser detail panel.

### #2 — Attack text formatting
The AttackBrowser detail panel shows `attack_text` as unformatted text. Long multi-paragraph prompts (persona injection, system-prompt attacks, GCG-suffixed prompts) are hard to scan. Fix: render in a `<pre>` with `whitespace-pre-wrap`, `max-h-64 overflow-y-auto`, and a character count badge. Also render the strategy `example` field below the description so reviewers can see the template alongside the actual text.

### #3 — Remove Coverage Heatmap tab
The standalone Coverage Heatmap page duplicates Panel C in StrategyComparison. Remove the "Coverage" nav tab from `App.tsx`. Do not delete `CoverageHeatmap.tsx` or `CoverageGrid.tsx` — leave them in place; the component may be embedded in Analytics.

### #4 — Strategy comparison: polarised colours
`fill="var(--color-danger)"` is applied to all bars regardless of ASR value. Fix: Recharts `<Cell>` per bar with threshold fill:
- ASR < 30%: green (`#22c55e`)
- ASR 30–60%: amber (`#f59e0b`)
- ASR > 60%: red (`#ef4444`)

### #5 — Strategy comparison summary writeup
After the 3 charts, render a computed `<AnalyticsSummary>` component. Derives from already-loaded `useStrategyComparison` + `useCoverage` — no new API call. Statements:
- "Highest-ASR strategy: [X] — [Y]% across [N] runs."
- "Lowest-ASR strategy: [X] — [Y]% across [N] runs."
- "Most-tested strategy: [X] with [N] runs."
- "Highest-risk category across strategies: [Z]."

### #6 — Regression tracker summary writeup
After the 4 panels, render a computed `<RegressionSummary>` component. Derives from `useRegression` + `useCategoryDelta`. Statements:
- "Latest session ([date]): [X]% ASR — [Δ] vs baseline."
- "Most regressed category: [Z] (+[Δ]%)."
- "Most improved category: [Z] (−[Δ]%)."
- Edge case (single session): "Only one session recorded — run a second to track change."

### #7 — Merge into single Analytics tab
New `pages/Analytics.tsx` stacks:
1. Section: "Strategy Performance" → StrategyComparison content (3 charts + AnalyticsSummary)
2. `<hr>` section divider
3. Section: "Regression Tracking" → RegressionTracker content (4 panels + RegressionSummary)

`App.tsx` nav: remove "Coverage", "Strategy", "Regression" tabs (3 removed); add "Analytics" tab. Net nav: 7 → 5 tabs: **Attack Browser | Analytics | Sample Review | Failure Clusters | Bias Heatmap**.

`StrategyComparison.tsx` and `RegressionTracker.tsx` become importable section components (remove their outer page `<div className="p-4">` wrappers so Analytics.tsx controls padding).

### #8 — Sample review dedup bug
`groupRuns()` in `SampleReview` groups by `attack_text` client-side, but the 200-row page limit means some groups are incomplete — the same attack may appear in both the first 200 rows and beyond, yielding truncated groups. Fix: backend `GET /runs` gains optional `dedup=true` query param. When `dedup=true`, the endpoint returns the **most-recent run per `attack_id`** within the session (using `DISTINCT ON (attack_id) ORDER BY attack_id, created_at DESC`). Frontend Compare mode passes `dedup=true` and removes the 200-row hack.

New backend logic: SQLAlchemy `select(Run).distinct(Run.attack_id).order_by(Run.attack_id, Run.created_at.desc())` — or raw SQL with `DISTINCT ON`. `dedup=true` is ignored in All mode.

### #9 — Failure cluster graph: better axes
Current: X = cluster_id (arbitrary integer), Y = failure count, Z = failure count (redundant). The chart tells you nothing that the cards don't already show.

Better: map each cluster to its **strategy** (X) and **harm category** (Y) using categorical ordinal positions:
- X = strategy index in a list sorted by total cluster failures for that strategy
- Y = category index in a list sorted by total cluster failures for that category
- Z = cluster size (bubble area)
- Colour = category colour (unchanged)

Axis labels via `tickFormatter` mapping index → string name. This turns the chart into a genuine 2D view of which strategy × category intersections generate the most clustered failures.

### #10 — Cluster cards sorted by % failures
Sort the card grid descending by `c.size / totalFailures` before rendering. The proportion is already computed per card; sort the `data.summaries` array before the `.map()`.

### #11 — Bias back-translation
New backend endpoint `POST /bias/back-translate` with body `{ text: string, source_lang: 'zh' | 'ru' | 'ar' }`. Calls `anthropic.messages.create()` using `claude-haiku-4-5-20251001`. Translation prompt: `"Translate the following {source_lang} text to English. Return only the translation, no explanation:\n\n{text}"`. Response schema: `{ translated: string }`.

Frontend: `BiasResponseViewer` gains a `useBackTranslation` hook. When the user switches to a non-EN tab, the hook fires `POST /bias/back-translate` with the response text for that language. Result cached in `useState<Record<string, string>>` keyed by `${lang}:${topicId}`. Third column shows loading spinner while translating, then rendered text. If `langDetail.response` is null, third column shows "No response to translate."

---

## Success Criteria (done when)

1. All strategy keys present in the DB documented in `strategyDescriptions.ts` with 2–3-sentence descriptions; `example` rendered in AttackBrowser detail panel
2. Attack text detail panel: scrollable `<pre>`, character count badge, strategy example shown
3. Navigation has no "Coverage" tab
4. Strategy ASR bars coloured green/amber/red by threshold via `<Cell>`
5. `AnalyticsSummary` renders below StrategyComparison panels with 4 computed statements
6. `RegressionSummary` renders below RegressionTracker panels with 3+ computed statements
7. Single "Analytics" nav tab replaces "Strategy" + "Regression" + "Coverage"; both sections visible
8. Sample review Compare mode uses `dedup=true`; one row per unique attack; no duplicate groups visible
9. Cluster scatter X = strategy, Y = category, Z = size; axis labels readable
10. Cluster cards sorted descending by % of all failures
11. Back-translation populated in BiasResponseViewer; loading state visible; result cached

---

## Constraints

- No new DB migrations (back-translation is ephemeral)
- TypeScript strict mode, no `any`
- Ruff clean on all backend changes
- `style={{}}` only for dynamic/SVG-justified cases
- Back-translation must use `claude-haiku-4-5-20251001`

---

## Handoff

Next role: planner  
Open questions for planner to resolve:
- Q1: Which strategy keys are in the DB beyond the current 6? Check `GET /attacks/strategies` API.
- Q2: `dedup=true` — most-recent run per attack_id, or highest `classifier_score`?
- Q3: Should `StrategyComparison` and `RegressionTracker` export named section components for embedding in `Analytics.tsx`, or should `Analytics.tsx` duplicate the JSX?
- Q4: `POST /bias/back-translate` — should it be rate-limited or cached at the backend level, or is client-side cache sufficient?
