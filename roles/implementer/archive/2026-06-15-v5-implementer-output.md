# Implementer Output — Glossary Tab

**Role:** implementer  
**Sequence:** add-feature  
**Date:** 2026-06-14

---

## Files Produced / Modified

### Frontend — new files
| File | Purpose |
|------|---------|
| `web/src/pages/Glossary.tsx` | Glossary page: three sections (Metrics, Attack Strategies, Harm Categories) with live ASR badges |
| `web/src/test/Glossary.test.tsx` | 4 Vitest tests: section headings, metric terms, 13 strategy keys, sample category labels |

### Frontend — modified files
| File | Change |
|------|--------|
| `web/src/App.tsx` | Added `'glossary'` to Tab union; added Glossary to TABS array; added conditional render; added import |
| `web/src/test/App.test.tsx` | Fixed stale tab name assertions (Coverage Heatmap → Analytics; Strategy Comparison → Bias Heatmap; Regression Tracker → Glossary) |

---

## Glossary.tsx Architecture

```
Glossary()
├── useStrategyComparison()       — fetches /strategy-comparison for live ASR data
├── asrByStrategy memo            — maps strategy key → ASR float
├── Section: "Metrics"            — table: ASR, Classifier Score, Jailbreak Success, Latency
├── Section: "Attack Strategies"  — table: 13 WAVE_STRATEGIES × key / name+description / AsrBadge
└── Section: "Harm Categories"    — table: LABEL_0–LABEL_12 × human label / CATEGORY_DESCRIPTIONS

AsrBadge({ asr })
  ≥ 0.40 → bg-danger/10 text-danger   "N% High"
  ≥ 0.10 → bg-warning/10 text-warning "N% Med"
  < 0.10 → bg-success/10 text-success "N% Low"
```

- Reuses `STRATEGY_DESCRIPTIONS` from `@/lib/strategyDescriptions` (already existed, 35 entries)
- Reuses `CATEGORY_LABELS` from `@/lib/categoryLabels` (already existed, LABEL_0–LABEL_12)
- `CATEGORY_DESCRIPTIONS` defined inline in Glossary.tsx (13 entries, one per label)
- No new backend endpoints required

---

## Verification

| Check | Result |
|-------|--------|
| `pnpm tsc --noEmit` | ✓ 0 errors |
| `pnpm test` | ✓ 5/5 tests pass (4 Glossary + 1 App) |
| App.test.tsx tab names | ✓ Updated to match current 6 tabs |

---

## Deviations from Architecture

None. Frontend-only change. No new API surface, no backend modifications. All Tailwind tokens from existing `@theme {}` palette.

---

## Known Gaps

- `AsrBadge` shows `—` when `useStrategyComparison` returns no data (e.g. API unavailable). Graceful degradation, no error state needed.
- `CATEGORY_DESCRIPTIONS` is defined inline rather than in a shared lib. Only one consumer exists; extraction would be premature.

---

## Handoff

Next role: reviewer  
Audit: verify all 5 brief acceptance criteria, check token reuse (STRATEGY_DESCRIPTIONS, CATEGORY_LABELS), confirm no inline styles, check graceful degradation when API data absent, verify test coverage matches acceptance criteria.
