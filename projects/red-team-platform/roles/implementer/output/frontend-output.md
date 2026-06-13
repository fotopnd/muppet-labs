# Implementer Output — Language Bias Probes (Frontend Phase)

**Date:** 2026-06-13
**Role:** Implementer
**Phase:** Frontend
**Project:** language-bias-probes (extends red-team-platform in-place)

---

## Files Written / Modified

| File | Change |
|------|--------|
| `web/package.json` | Added `tailwindcss ^4.3.0`, `@tailwindcss/vite ^4.3.0` |
| `web/vite.config.ts` | Added `tailwindcss()` plugin (before react plugin) |
| `web/src/index.css` | Prepended `@import "tailwindcss"` + `@theme {}` block with full canonical token set + divergence extension tokens + dark-mode overrides |
| `web/src/types/index.ts` | Added `BiasScoreRow`, `BiasScoresOut` types |
| `web/src/hooks/useBiasScores.ts` | New — React Query hook for `GET /bias/scores` |
| `web/src/components/BiasCell.tsx` | New — colour-bucketed `<td>` (null=grey, 0–0.14=green, 0.15–0.34=amber, 0.35+=red) |
| `web/src/pages/BiasHeatmap.tsx` | New — heatmap table grouped by government with legend |
| `web/src/App.tsx` | Added `'bias'` to Tab union; added `{ id: 'bias', label: 'Bias Heatmap' }` tab entry; added `{activeTab === 'bias' && <BiasHeatmap />}` render |

---

## Key Design Decisions

- **Tailwind v4 added alongside existing CSS** — `@import "tailwindcss"` prepended before existing `:root {}` block. All pre-existing inline-style tabs left untouched.
- **Canonical token names** per `design_style.md` — `--color-canvas`, `--color-text-primary`, `--font-sans`, etc. All new components use Tailwind utility classes only; no `style=""`.
- **Fragment keyed on government** — `<Fragment key={government}>` wraps each group header + topic rows to avoid React key warnings.
- **Empty state** shows seed/attack/score-bias CLI commands as code snippets so the tab is self-documenting.
- **Dark mode** via `@media (prefers-color-scheme: dark) :root {}` CSS variable overrides (Tailwind v4's approach without class toggle).

---

## Build Status

- `tsc --noEmit` — clean (0 errors)
- `vite build` — clean (only pre-existing chunk-size warning unrelated to this feature)
- Dev server verified running at `http://localhost:5173`

---

## Handoff

**Next role:** UI Reviewer

**What to verify:**
1. "Bias Heatmap" tab appears in nav and is clickable
2. Empty state renders with CLI instructions when no scores exist
3. With seeded data: government group headers render in accent-subtle; topic rows render with colour-bucketed BiasCell values
4. Legend (null/0–0.14/0.15–0.34/0.35+) renders above table
5. Dark mode: tokens flip correctly; no hardcoded light-mode colours bleed through
6. No horizontal scrollbar at desktop width; table scrolls horizontally on narrow viewports via `overflow-x-auto`
7. `design_style.md` compliance: no inline styles, no arbitrary Tailwind values, canonical tokens used
