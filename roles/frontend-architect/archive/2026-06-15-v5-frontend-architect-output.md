# Frontend-Architect Output — language-bias-probes

**Role:** frontend-architect  
**Sequence:** new-project-full  
**Date:** 2026-06-13  
**Step:** 5 of 9

---

## Setup: Add Tailwind v4 to red-team-platform web/

The existing dashboard uses inline styles and raw CSS variables. The BiasHeatmap and all future additions will use Tailwind v4 with canonical `@theme` tokens. The existing components are not migrated — they continue to function unchanged.

**Required changes to `web/`:**

1. `pnpm add -D @tailwindcss/vite` in `web/`
2. In `web/vite.config.ts`, add:
   ```ts
   import tailwindcss from '@tailwindcss/vite'
   // in plugins: [react(), tailwindcss()]
   ```
3. Add `@import "tailwindcss";` at the top of `web/src/index.css` (before the existing `:root` block). The existing CSS variables are preserved and continue to work.

---

## Token Layer

Add the following `@theme` block to `web/src/index.css` immediately after the `@import "tailwindcss";` line and before the existing `:root` block:

```css
@import "tailwindcss";

@theme {
  /* Canvas — 60% */
  --color-canvas:        oklch(98.2% 0 0);
  --color-surface:       oklch(100% 0 0);
  --color-surface-muted: oklch(96.0% 0 0);

  /* Structure — 30% */
  --color-border:          oklch(91.5% 0 0);
  --color-text-primary:    oklch(5.0% 0 0);
  --color-text-secondary:  oklch(44.0% 0.01 302);
  --color-text-muted:      oklch(58.0% 0.01 302);
  --color-text-inverse:    oklch(98.2% 0 0);

  /* Accent — 10%, purple matching existing --accent: #aa3bff */
  --color-accent:        oklch(66.0% 0.27 302);
  --color-accent-hover:  oklch(59.0% 0.27 302);
  --color-accent-subtle: oklch(96.5% 0.05 302);

  /* Semantic states */
  --color-success: oklch(55.0% 0.17 142);
  --color-warning: oklch(73.0% 0.17 60);
  --color-danger:  oklch(55.0% 0.20 28);

  /* Divergence heatmap extension tokens */
  --color-divergence-low:  oklch(95.5% 0.06 145);   /* 0.00–0.14: subtle green tint */
  --color-divergence-mid:  oklch(95.0% 0.07 80);    /* 0.15–0.34: subtle amber tint */
  --color-divergence-high: oklch(94.5% 0.08 25);    /* 0.35+:     subtle red tint   */
  --color-divergence-low-text:  oklch(35.0% 0.13 145);
  --color-divergence-mid-text:  oklch(40.0% 0.13 60);
  --color-divergence-high-text: oklch(40.0% 0.15 25);

  /* Typography — canonical names */
  --font-sans: system-ui, "Segoe UI", Roboto, sans-serif;
  --font-mono: ui-monospace, "SF Mono", "JetBrains Mono", Consolas, monospace;
}
```

**Dark mode:** The existing `@media (prefers-color-scheme: dark)` block in index.css already adjusts `--bg`, `--text`, etc. for the legacy components. Add dark-mode overrides for the new `@theme` tokens using a `@media` block after the `@theme` block:

```css
@media (prefers-color-scheme: dark) {
  :root {
    /* Override @theme tokens for dark mode */
    --color-canvas:        oklch(13.0% 0.01 302);
    --color-surface:       oklch(17.0% 0.01 302);
    --color-surface-muted: oklch(21.0% 0.01 302);
    --color-border:        oklch(28.0% 0.01 302);
    --color-text-primary:  oklch(96.0% 0 0);
    --color-text-secondary: oklch(72.0% 0.01 302);
    --color-text-muted:    oklch(55.0% 0.01 302);
    --color-accent:        oklch(75.0% 0.27 302);
    --color-accent-hover:  oklch(80.0% 0.27 302);
    --color-accent-subtle: oklch(22.0% 0.08 302);
    --color-divergence-low:  oklch(22.0% 0.07 145);
    --color-divergence-mid:  oklch(22.0% 0.07 80);
    --color-divergence-high: oklch(22.0% 0.08 25);
    --color-divergence-low-text:  oklch(72.0% 0.13 145);
    --color-divergence-mid-text:  oklch(72.0% 0.13 60);
    --color-divergence-high-text: oklch(72.0% 0.15 25);
  }
}
```

**Note:** Tailwind v4 `@theme` tokens are resolved at build time and cannot be dynamically overridden by a `@media` block. Dark-mode values must be applied as CSS variable overrides on `:root` (as shown above), which Tailwind's generated utility classes will pick up because they reference `var(--color-*)` at runtime.

---

## Page Layout

The BiasHeatmap tab lives inside the existing `<main>` element in `App.tsx`. The existing tabs use ad-hoc padding. The BiasHeatmap uses a consistent container:

```
<div class="px-6 py-5 max-w-5xl mx-auto">
  <div class="mb-4 flex items-center gap-3">   ← header row: title + ScoredModelBadge
  <div>                                          ← DivergenceTable wrapper (no max-width override)
```

The table itself spans full container width. Column widths:
- Label column: `w-[55%]` (topic label is the longest content)
- ZH / RU / AR columns: `w-[15%]` each (equal, contain a short score)

At 1024px viewport (1126px `#root` - 2×24px padding = 1078px usable), the table fits comfortably.

---

## Component Specs

### 1. DivergenceTable

- **Hierarchy:** `DivergenceTable` → `GovernmentGroupHeader` + `DivergenceRow` (×50) + `BiasCell` (×150 max)
- **Element:** `<table class="w-full border-collapse text-sm">` inside a `<div class="rounded-lg border border-border overflow-hidden">`
- **Column headers:** `<thead>` with one `<tr>`: empty label cell + `<th>` for ZH, RU, AR. Use `text-text-muted font-medium text-xs uppercase tracking-wide py-2 px-3 text-right`.
- **Layout:** `border-collapse` on the table. Row borders via `border-t border-border` on each `<tr>` (not on individual cells).
- **Loading state:** Replace table with 3 skeleton rows — `<div class="animate-pulse bg-surface-muted h-8 rounded mb-1">` repeated.
- **Data:** `BiasScoresOut` from `useBiasScores()`. Group rows by `government` client-side before rendering.

### 2. GovernmentGroupHeader

- **Element:** `<tr>` with single `<td colspan={4}>` — spans all 4 columns.
- **Tokens:** `bg-surface-muted text-text-secondary text-xs font-semibold uppercase tracking-wider px-3 py-1.5`
- **Not** a border-separated section — background tint is sufficient separation per design_style.md "Subtle Contrast Over Heavy Shapes".
- **Data:** government name string (e.g. `"China"`).

### 3. DivergenceRow

- **Element:** `<tr class="border-t border-border hover:bg-surface-muted transition-colors duration-100">`
- **Cells:**
  - Label cell: `<td class="px-3 py-2 text-text-secondary text-sm">` — topic `label` string.
  - Three score cells: `<td class="px-3 py-1.5 text-right">` — contains `<BiasCell score={row.zh_score} />` etc.
- **Data:** one `BiasScoreRow` object.

### 4. BiasCell

- **Element:** `<span>` (inline, inside its `<td>`).
- **Classes by score bucket:**

  | Condition | Background token | Text token | Display |
  |-----------|-----------------|------------|---------|
  | `score === null` | `bg-surface-muted` | `text-text-muted` | `—` |
  | `score < 0.15` | `bg-divergence-low` | `text-divergence-low-text` | `0.XX` |
  | `score < 0.35` | `bg-divergence-mid` | `text-divergence-mid-text` | `0.XX` |
  | `score >= 0.35` | `bg-divergence-high` | `text-divergence-high-text` | `0.XX` |

- **Shared classes:** `inline-block font-mono text-xs font-semibold rounded px-1.5 py-0.5 tabular-nums`
- **Score display:** `score.toFixed(2)` — always 2 decimal places.
- **Props:** `{ score: number | null }`

### 5. ScoredModelBadge

- **Element:** `<span>` inline in the header row.
- **Tokens when model present:** `bg-accent-subtle text-accent text-xs font-medium rounded-full px-2.5 py-0.5`
- **Text:** `gemma2:9b` (the `scored_model` value from the API).
- **Tokens when null:** `bg-surface-muted text-text-muted text-xs font-medium rounded-full px-2.5 py-0.5`
- **Text when null:** `No scores yet`
- **Props:** `{ model: string | null }`

### 6. EmptyState

- **Condition:** `rows.length === 0` (after loading, not during).
- **Element:** `<div class="rounded-lg border border-border bg-surface-muted p-8 text-center">`
- **Content:**
  - `<p class="text-text-secondary text-sm mb-4">Run the following commands to populate the heatmap:</p>`
  - Two `<code>` blocks (rendered as `<pre class="bg-canvas rounded px-4 py-2 font-mono text-xs text-text-primary text-left inline-block mb-2">`) containing:
    1. `uv run seed-bias-corpus`
    2. `uv run attack --mode bias --language en && uv run attack --mode bias --language zh && ...`
    3. `uv run score-bias`

---

## App.tsx Modifications

Add `'bias'` to the `Tab` union type and a new entry to `TABS`:

```ts
type Tab = 'attacks' | 'coverage' | 'strategy' | 'regression' | 'sample' | 'clusters' | 'bias'

{ id: 'bias', label: 'Bias Heatmap' }
```

Add to the render block:
```tsx
{activeTab === 'bias' && <BiasHeatmap />}
```

Import:
```tsx
import { BiasHeatmap } from '@/pages/BiasHeatmap'
```

**Do not change existing inline styles** in the nav or header — out of scope for this pass.

---

## Constraints Applied

1. **Subtle Contrast Over Heavy Shapes (design_style.md):** GovernmentGroupHeader uses `bg-surface-muted` tint, not a border row. DivergenceRow uses `hover:bg-surface-muted` on hover, not a border highlight.

2. **Banned Constructions — no hardcoded hex:** All BiasCell bucket colours are canonical `@theme` extension tokens (`--color-divergence-*`), not inline `style={}` or arbitrary Tailwind values like `bg-[#ffdddd]`.

3. **Strictly Banned — no arbitrary pixel spacing:** All spacing uses Tailwind scale (`px-3`, `py-2`, etc.). No `px-[13px]` or inline `style={{ padding: '13px' }}`.

4. **60-30-10 rule:** The heatmap is predominantly canvas/surface (white backgrounds), text is slate-toned, and accent (purple) appears only in `ScoredModelBadge`. The divergence colours are deliberate extensions that use very low-saturation tints to avoid violating the 10% accent ceiling.

5. **Tailwind v4 dark-mode override pattern:** The `@theme` block sets build-time defaults; the `@media (prefers-color-scheme: dark) :root {}` block overrides the CSS variables at runtime. This is the correct v4 pattern — do not use `dark:` variant classes, which require a `class="dark"` toggle not present in this app.

---

## Open Questions

1. **Tooltip (stretch):** The design-brief noted a hover tooltip showing `divergence_hypothesis` as high-value for portfolio demonstration. Not in done criteria; implement only if time permits after the table passes ui-reviewer. If added: use a `title` attribute first (simplest); upgrade to a styled tooltip div only if the plain `title` is insufficient.

2. **Row ordering within government groups:** The architect output specifies ordering by `topic_id` (e.g. `cn_01`–`cn_05`). The implementer should sort client-side; do not rely on API response order.

---

## Handoff

The implementer reads this file alongside `roles/architect/output/output.md`.

**Backend phase first** (step 6a): implement all Python — `bias/models.py`, `bias/seed.py`, `bias/runner.py`, `bias/scorer.py`, `api/routers/bias.py`, Alembic migration, `pyproject.toml` changes, `tests/test_bias.py`. Run `ruff check + format`. Write `roles/implementer/output/backend-output.md`.

**Frontend phase second** (step 6b): implement Tailwind v4 setup + all React components per this spec. Run `pnpm build` + `pnpm lint`. Write `roles/implementer/output/output.md` (final, covering both phases).

Deviations from this spec must be noted in the implementer output with a reason.
