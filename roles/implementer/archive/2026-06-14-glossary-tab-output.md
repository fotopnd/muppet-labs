# Implementer Output — red-team-platform dashboard refinement v2

**Role:** implementer  
**Sequence:** add-feature  
**Date:** 2026-06-13

---

## Files Produced / Modified

### Backend
| File | Change |
|------|--------|
| `pyproject.toml` | Added `anthropic>=0.107.1` |
| `.env` | Added `ANTHROPIC_API_KEY` |
| `api/schemas.py` | Added `BackTranslateIn`, `BackTranslateOut`; added `Literal` import |
| `api/routers/runs.py` | Added `dedup: bool = False` param; `DISTINCT ON` SQL for dedup mode |
| `api/routers/bias.py` | Added `POST /bias/back-translate` endpoint using Anthropic haiku |

### Frontend — new files
| File | Purpose |
|------|---------|
| `src/pages/Analytics.tsx` | Combined Analytics tab: Strategy + Regression sections with jump links |
| `src/components/AnalyticsSummary.tsx` | Computed prose: highest/lowest ASR strategy, most-tested, highest-risk category |
| `src/components/RegressionSummary.tsx` | Computed prose: latest ASR, regression delta, best/worst category |
| `src/hooks/useBackTranslation.ts` | TanStack Query hook for POST /bias/back-translate; staleTime: Infinity |

### Frontend — modified files
| File | Change |
|------|--------|
| `src/lib/strategyDescriptions.ts` | Expanded from 6 → 35 strategy entries with 2–3-sentence descriptions and examples |
| `src/types/index.ts` | Added `BackTranslateIn`, `BackTranslateOut` types |
| `src/hooks/useRuns.ts` | Added `dedup?: boolean` query param |
| `src/App.tsx` | Removed Coverage/Strategy/Regression tabs; added Analytics tab (5 tabs total) |
| `src/pages/StrategyComparison.tsx` | Removed outer p-4 wrapper and heading; Cell colour thresholds (green/amber/red); AnalyticsSummary added |
| `src/pages/RegressionTracker.tsx` | Removed outer p-4 wrapper and heading; RegressionSummary added |
| `src/pages/AttackBrowser.tsx` | Detail panel: scrollable pre with char count badge; example field in code block |
| `src/pages/FailureClusters.tsx` | Bubble chart: X=strategy, Y=category categorical axes; cards sorted by % failures |
| `src/pages/SampleReview.tsx` | Compare mode: dedup=true with session required |
| `src/components/BiasResponseViewer.tsx` | Third column: live back-translation via useBackTranslation hook |

---

## Verification

| Check | Result |
|-------|--------|
| `npx tsc --noEmit` | ✓ 0 errors |
| `uv run ruff check src/` | ✓ 0 errors |
| `GET /runs?session_id=X&dedup=true` | ✓ 300 deduplicated items returned |
| `POST /bias/back-translate` `{"text":"你好，世界","source_lang":"zh"}` | ✓ `{"translated":"Hello, world"}` |
| Nav: 7 → 5 tabs | ✓ Coverage/Strategy/Regression removed; Analytics added |

---

## Deviations from Architecture

**D1** — The `.env` approach for the Anthropic API key: the uvicorn process inherits env from shell at start time, and the key is also in `.env` which pydantic-settings loads via `extra="ignore"`. The `anthropic.Anthropic()` client reads from env directly (not from settings). This works as long as the server is started with the key in env or the .env is loaded at process start.

**D2** — `isCompare && !!selectedSessionId` guards the `dedup=true` call: when no session is selected, dedup is not sent to avoid the 400 error. Compare mode with no session selected shows all runs (non-dedup) until a session is picked.

---

## Known Gaps

- `StrategyComparison` and `RegressionTracker` are imported directly into `Analytics.tsx` — they're no longer standalone route targets. If either is linked to directly in future, they'll render without padding. This is acceptable since they have no standalone tab.
- Back-translation adds a network call per (lang, topicId) pair. With staleTime=Infinity, each pair is only fetched once per session. No rate limiting on the backend endpoint.

---

## Handoff

Next role: reviewer  
Run style audit, confirm all 11 brief items against done-when criteria, check `style={{}}` justifications, verify backend error paths (dedup with no session_id, back-translate with null text).
