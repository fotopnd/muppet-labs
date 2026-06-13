# UI Reviewer Output — Language Bias Probes Frontend

**Date:** 2026-06-13
**Role:** ui-reviewer
**Project:** language-bias-probes / red-team-platform

---

## Verdict

REWORK NEEDED

---

## Violations

- [ ] `web/src/pages/BiasHeatmap.tsx:56` — **Criterion 6 FAIL: ScoredModelBadge null case.**
  When `data.scored_model` is null the conditional `{data.scored_model && ...}` renders nothing. Design-brief criterion 6 requires the text "No scores yet" to render when `scored_model` is null. Fix: replace the short-circuit with a ternary that always renders the badge, showing model name when non-null and "No scores yet" otherwise.

- [ ] `web/src/index.css` — **Criterion 9 FAIL: Divergence tokens missing dark-mode overrides.**
  The `@media (prefers-color-scheme: dark) :root {}` block does not override `--color-divergence-null`, `--color-divergence-low`, `--color-divergence-mid`, or `--color-divergence-high`. Against a dark canvas the null grey (`oklch(70%...)`) may disappear. Criterion 9 explicitly requires dark-mode overrides for all divergence tokens. Fix: add all four token overrides to the dark-mode block, increasing lightness slightly so cells remain visually distinct on the dark canvas.

---

## Done Criteria Check

- [x] 1. Table structure groups rows under government headers — PASS (structure correct; data-dependent)
- [x] 2. Government sub-header rows span 4 columns (`colSpan={4}`), distinct via `bg-accent-subtle` — PASS
- [x] 3. BiasCell shows cosine distance to 2 decimal places in `font-mono` — PASS
- [x] 4. Colour buckets correct: <0.15 low, <0.35 mid, ≥0.35 high; tokens in `@theme` — PASS
- [x] 5. Null cell renders grey "—", not blank/0.00 — PASS
- [ ] 6. ScoredModelBadge renders "No scores yet" when `scored_model` is null — **FAIL**
- [x] 7. EmptyState renders CLI commands in `<code>` elements — PASS
- [x] 8. No horizontal scroll at ≤1126px; table is `w-full` inside `overflow-x-auto` — PASS
- [ ] 9. Dark-mode overrides for all divergence tokens — **FAIL**
- [x] 10. Bias tab in top navigation, consistent styling — PASS

---

## Passed Checks

- No `style=""` in any new component — Tailwind utilities throughout
- No arbitrary pixel values — all spacing from standard scale (`p-2`, `p-4`, `gap-4`, `w-20`, `h-3`, etc.)
- No hardcoded hex or raw hue values in new components
- Canonical token names used: `text-text-primary`, `bg-surface-muted`, `border-border`, `text-accent`, `bg-accent-subtle`, `font-mono`
- Accent applied only to government group headers (focal structural element) — 60-30-10 respected
- `font-mono` correctly applied to score values and model badge (metric / ID contexts)
- `Fragment` keyed on `government` — no React key warning
- Empty state is self-documenting with three CLI commands in `<code>` elements
- `rounded-sm` on `<td>` is a no-op under `border-collapse` — harmless, not a violation

---

## Handoff

REWORK NEEDED — ui-debugger applies the two fixes above, then ui-reviewer re-runs.
