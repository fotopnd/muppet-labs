# Reviewer Output — red-team-platform dashboard refinement v2

**Role:** reviewer  
**Sequence:** add-feature  
**Date:** 2026-06-13

---

## Verdict: PASS WITH NOTES

All 11 brief items are complete. Three minor reviewer fixes applied during this review (not blocking). No regressions detected.

---

## Checklist: Done-When Criteria

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| 1 | All 35 strategy keys documented; `example` rendered in AttackBrowser | ✓ PASS | 35 entries confirmed; example shown in `<code>` block in detail panel |
| 2 | Attack text: scrollable `<pre>`, char count badge, strategy example | ✓ PASS | `max-h-64 overflow-y-auto`; badge in `flex justify-between` header; example in `<code>` block |
| 3 | No "Coverage" tab in nav | ✓ PASS | Nav is 5 tabs: Attack Browser / Analytics / Sample Review / Failure Clusters / Bias Heatmap |
| 4 | Strategy ASR bars coloured green/amber/red via `<Cell>` | ✓ PASS | `asrColour()` thresholds: <30 green, 30–60 amber, >60 red; hex constants |
| 5 | `AnalyticsSummary` renders below StrategyComparison with 4 computed statements | ✓ PASS | Excludes `none`/`original_prompt`; calls own hooks; `bg-surface-muted` box |
| 6 | `RegressionSummary` renders below RegressionTracker with 3+ statements | ✓ PASS | Single-session edge case; most-regressed `text-danger`, most-improved `text-success` |
| 7 | Single "Analytics" tab; both sections visible with jump-link navigation | ✓ PASS | `#strategy` / `#regression` anchors; sections stacked with `<hr>` divider |
| 8 | Compare mode uses `dedup=true`; one row per unique attack | ✓ PASS | `DISTINCT ON (attack_id) ORDER BY attack_id, created_at DESC`; guard `isCompare && !!selectedSessionId` |
| 9 | Cluster scatter X=strategy, Y=category, Z=size; readable axis labels | ✓ PASS | `stratOrder`/`catOrder` sorted by total cluster failures; `tickFormatter` maps index → name |
| 10 | Cluster cards sorted descending by % of all failures | ✓ PASS | `[...data.summaries].sort((a,b) => b.size - a.size)` before `.map()` |
| 11 | Back-translation in BiasResponseViewer; loading state; cached | ✓ PASS | `BackTranslationBlock` per lang; `staleTime: Infinity`; "Translating…" spinner |

---

## Adversarial Test Results

| Test | Expected | Actual | Verdict |
|------|----------|--------|---------|
| `GET /runs?dedup=true` (no `session_id`) | HTTP 400 | HTTP 400 | ✓ |
| `POST /bias/back-translate` `{"text":"","source_lang":"zh"}` | `{"translated":""}` | `{"translated":""}` (after fix) | ✓ |
| `POST /bias/back-translate` `{"text":"hello","source_lang":"fr"}` | HTTP 422 | HTTP 422 | ✓ |

---

## Style Audit

### `style={{}}` instances in v2 components

| File | Instance | Justification |
|------|----------|---------------|
| `StrategyComparison.tsx` | `<Cell fill={asrColour(...)}` | Dynamic computed colour — Tailwind cannot interpolate runtime values |
| `FailureClusters.tsx` | Recharts bubble `fill`, `stroke` per cluster | Recharts SVG props; dynamic palette |
| `Analytics.tsx` | None | Clean |
| `AnalyticsSummary.tsx` | None | Clean |
| `RegressionSummary.tsx` | None | Clean |
| `BiasResponseViewer.tsx` | None | Clean |
| `AttackBrowser.tsx` (v2 changes) | None new | Existing justified instances unchanged |

All remaining `style={{}}` usages are justified by dynamic runtime values or Recharts SVG requirements per `typescript-conventions.md`.

---

## Reviewer Fixes Applied

**Fix 1 — Stale UI copy in SampleReview:**  
Line 113 read "Compare mode — showing first 200 runs. Use session filter to narrow." — holdover from before `dedup=true`. Compare mode now returns all unique attacks for the selected session (no page ceiling). Updated to conditional: "Compare mode — select a session to load deduplicated attacks." (shows only when no session is selected).

**Fix 2 — Dead conditional assignment:**  
`const pageSize = isCompare ? 20 : 20` in `SampleReview.tsx` — both branches identical. Collapsed to `const pageSize = 20`.

**Fix 3 — Empty-text back-translate hallucination:**  
`POST /bias/back-translate {"text": ""}` returned HTTP 200 with hallucinated content (Confucius quotes in English). Added `if not body.text.strip(): return BackTranslateOut(translated="")` early return. Frontend `enabled: !!text` guard already prevented this from being sent in practice, but the endpoint now also handles it correctly.

---

## Notes

**N1 — Back-translate rate limiting:**  
No rate limiting on `POST /bias/back-translate`. Each (lang, topicId) pair fires at most one Anthropic API call per browser session due to `staleTime: Infinity`. In production, add a short Redis cache keyed on `(source_lang, sha256(text))` to handle concurrent users. Not a blocker for portfolio use.

**N2 — Analytics tab padding ownership:**  
`StrategyComparison.tsx` and `RegressionTracker.tsx` had their outer `p-4` wrappers removed; `Analytics.tsx` controls padding via section `<div className="p-4">` wrappers. If either component is ever embedded elsewhere, they'll render flush to their container. Intentional.

**N3 — `AnalyticsSummary` excludes `none`/`original_prompt`:**  
Correct. Including baseline strategies in "highest ASR" summary would be misleading. Exclusion is consistent with the intent (show which adversarial strategy performed best/worst).

**N4 — Cluster chart categorical encoding:**  
`stratOrder`/`catOrder` derived from cluster data only. Strategies with zero failed clusters don't appear on the X axis. Correct — the chart shows failure concentration, not strategy coverage.

---

## Handoff

Next role: retro  
Workspace learnings from v2 to consider:
- Categorical axis encoding in Recharts (ordinal index + `tickFormatter`)
- Anthropic SDK deferred-import pattern inside FastAPI route handlers
- `DISTINCT ON (attack_id)` for latest-per-group dedup queries
- `staleTime: Infinity` pattern for immutable computed results
