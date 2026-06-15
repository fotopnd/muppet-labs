# Design Brief Output — language-bias-probes

**Role:** design-brief  
**Sequence:** new-project-full  
**Date:** 2026-06-13  
**Step:** 4 of 9

---

## Interface Context

**Application Dashboard.**  
This is a new tab added to the existing red-team-platform operational dashboard. The user is a technical reviewer (interviewer, portfolio reader) examining research output, not a first-time visitor. Data density is appropriate; the heatmap grid is the primary surface, not decorative copy. Marketing/Landing Page context does not apply — there is no conversion goal here.

---

## Primary Interaction

A user arrives at the `/bias` tab to **read which (government, language) pairs produced the highest semantic divergence** — to understand at a glance where the model answers the same question differently depending on the user's language.

The table is the entire interaction. There is no form, no filter, and no click-through in v1. The user scans the grid, identifies high-divergence cells (hot colour), and reads the label to understand what topic drove the divergence.

---

## Key Visual Components

1. **DivergenceTable** — the main grid. Rows are topic labels (50 total), grouped under 10 government sub-headers. Columns are ZH, RU, AR. Renders from the `/bias/scores` API response.

2. **BiasCell** — a single table cell showing a cosine distance value (e.g. `0.42`) with a colour-coded background: three discrete buckets (low / moderate / high), plus a grey null state. Uses monospace font for the number, consistent with metric values elsewhere in the dashboard.

3. **GovernmentGroupHeader** — a full-width row spanning all 4 columns that labels a group of 5 topic rows (e.g. "China", "Russia"). Visually distinct from topic rows via a subtle background tint and slightly bolder text — not a harsh border.

4. **ScoredModelBadge** — a small inline badge above the table showing which model produced the scores and when (e.g. `gemma2:9b`). Renders "No scores yet" when `scored_model` is null. Keeps the data anchored to its source without cluttering the table.

5. **EmptyState** — full-width callout rendered in place of the table when the API returns zero rows (probes not yet seeded or scores not yet run). Displays the CLI commands needed to produce data: `uv run seed-bias-corpus` and `uv run score-bias`. Uses `--code-bg` / `--mono` to render the commands inline, matching the existing `code` element style in the dashboard.

---

## Done Criteria

1. The table renders all 50 topic rows grouped under 10 government sub-headers. Each group has exactly 5 topic rows beneath it.
2. Government sub-header rows span all 4 columns (label + ZH + RU + AR) and are visually distinct from topic rows — different background tint, not a border.
3. Each scored `BiasCell` displays the cosine distance value to 2 decimal places in monospace font.
4. Each `BiasCell` applies the correct colour bucket: low (0.00–0.14), moderate (0.15–0.34), high (0.35+). The colour tokens are defined in `index.css` using the existing CSS variable pattern (`:root { --divergence-low: ...; }` with dark-mode overrides) — not hardcoded hex values.
5. Null `BiasCell` values (language not yet scored) render as a grey cell containing "—", never blank or "0.00".
6. `ScoredModelBadge` renders the model name above the table when `scored_model` is non-null, and the text "No scores yet" when null.
7. `EmptyState` renders with the two CLI commands displayed as `<code>` elements when the API returns zero rows.
8. No horizontal scroll at 1024px viewport width. The table fits within the existing `#root` max-width container (1126px).
9. Dark mode: all three divergence colour tokens have dark-mode overrides in the existing `@media (prefers-color-scheme: dark)` block — they must not look identical to the light-mode values.
10. The `/bias` NavLink appears in the existing top navigation alongside the other tabs and is styled consistently with them.

---

## Handoff

The frontend-architect reads this file alongside `roles/architect/output/output.md` and `resources/design_style.md`.

**Open decisions for frontend-architect to resolve:**

1. **Divergence colour token values** — the architect spec proposed amber-100/red-100 Tailwind classes. The existing dashboard uses raw CSS variables, not Tailwind. The frontend-architect must define `--divergence-low`, `--divergence-mid`, `--divergence-high` (+ dark mode) as CSS variables in `index.css`. Choose values that are legible against `--bg` (white / `#16171d`) and visually distinct from each other and from `--accent-bg` (purple-tinted) which is already in use.

2. **Table element vs CSS grid** — the heatmap is a genuine grid of labelled data. Use a `<table>` with `<tbody>` grouping, not a CSS grid div layout. Screen readers and keyboard navigation work correctly on `<table>`; a div grid requires ARIA roles that are easy to get wrong.

3. **GovernmentGroupHeader row structure** — the architect spec recommended against `rowspan`. Use a full-width `<tr>` with a single `<td colspan={4}>` for the government header. This is semantically clean and consistent with how Bootstrap/Tailwind table patterns handle groups.

4. **Hover tooltip** — not required for v1 done criteria, but noted as high-value for portfolio demonstration: a tooltip on each `BiasCell` showing the `divergence_hypothesis` text from the probe would let a reviewer understand the research intent inline. Flag this as stretch scope; implement only after the core grid passes ui-reviewer.
