# UI Debugger Output — moderation-stream `/stream` dashboard

**Role:** ui-debugger
**Sequence:** `new-project-full` (step 7 — debug loop)
**Date:** 2026-06-02

---

## Fixes Applied

- **`tailwind.config.js:38-41`** — moved `status-active-bg` and `status-active-text` into the existing `colors` block (appended after `ring`); removed the duplicate `colors` block that previously appeared at line 46. Single `colors` key now contains all 14 tokens. CSS bundle grew from 17.62 kB → 20.98 kB, confirming shadcn/ui token classes are now generated correctly.
  *Satisfies:* design_style.md — every colour value must be mapped to a semantic token; the token layer must be intact for all downstream classes to produce CSS output.

- **`ModelMetricsCard.tsx:20-28`** — added `dimmed?: boolean` prop to `MetricRow`; value span now applies `text-muted-foreground` when `dimmed` is true, `text-foreground` otherwise. Accuracy row passes `dimmed={metrics.accuracy === null}`.
  *Satisfies:* frontend-architect spec — "Null accuracy: value renders as `'N/A'` with class `text-muted-foreground font-data`."

---

## Unresolved

None. Both violations resolved with targeted changes. No structural redesign required.

---

## Handoff

`ui-reviewer` runs second pass on the updated files:
- `projects/case-queue/web/tailwind.config.js`
- `projects/case-queue/web/src/components/ModelMetricsCard.tsx`
