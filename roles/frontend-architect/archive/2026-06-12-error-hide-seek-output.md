# Frontend-Architect Output — error-hide-seek

**Role:** frontend-architect
**Sequence:** `new-project-full` (step 5)
**Date:** 2026-06-07

---

## Open Decision Resolutions (from design-brief)

- **SelectionFloater positioning:** React portal (`createPortal` into `document.body`) with `position: fixed` computed from `window.getSelection().getRangeAt(0).getBoundingClientRect()`. More accurate than container-relative positioning across scroll. The `style` prop is necessary for dynamic computed coordinates — this is an explicit exception to the no-inline-style rule (see Constraints Applied §1).

- **Overlapping annotation highlights:** First occurrence wins. Before segmenting, sort annotations by `abstract.toLowerCase().indexOf(ann.text_excerpt.toLowerCase())` ascending. During segmentation, track `coveredUntil: number`; skip any annotation whose `indexOf` result falls within `[pos, coveredUntil)`.

- **ResultsPage polling:** `refetchInterval: (query) => query.state.data?.uplift === null ? 30_000 : false`. Polls every 30s while `uplift` is null; stops automatically once all conditions are complete.

- **Category breakdown table:** Always-visible directly below `ConditionResultsTable`, separated by `border-t border-border pt-6`. Five categories max — no collapse needed.

---

## Token Layer

**Accent hue: Blue** — consistent with all workspace projects (case-queue, moderation-dashboard, red-team-platform, llm-safety-monitor). Assumption noted; override if a different hue is needed.

```js
// tailwind.config.js — error-hide-seek
module.exports = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background:      { DEFAULT: '#f8fafc' },   // slate-50
        surface:         { DEFAULT: '#ffffff' },   // white
        border:          { DEFAULT: '#e2e8f0' },   // slate-200
        accent:          { DEFAULT: '#2563eb' },   // blue-600
        'accent-subtle': { DEFAULT: '#eff6ff' },   // blue-50
        'text-intense':  { DEFAULT: '#0f172a' },   // slate-900
        'text-default':  { DEFAULT: '#334155' },   // slate-700
        'text-muted':    { DEFAULT: '#94a3b8' },   // slate-400
        success:         { DEFAULT: '#059669' },   // emerald-600
        warning:         { DEFAULT: '#f59e0b' },   // amber-500
        danger:          { DEFAULT: '#dc2626' },   // red-600
      },
      fontFamily: {
        interface: ['Inter', 'SF Pro Display', 'Geist Sans', 'sans-serif'],
        data: ['JetBrains Mono', 'SF Mono', 'Geist Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
```

---

## Page Layout

Two independent pages. No global tab bar — routes are navigated programmatically (after session creation, after review submission).

### Global Shell (both pages)

```
┌─────────────────────────────────────────────────────┐
│ Header: h-14 bg-surface border-b border-border      │
│   "Error-Hide-Seek" (left) | breadcrumb (right)     │
├─────────────────────────────────────────────────────┤
│ Content area: bg-background min-h-screen            │
└─────────────────────────────────────────────────────┘
```

- Global wrapper: `min-h-screen bg-background font-interface`
- Header: `h-14 bg-surface border-b border-border flex items-center justify-between px-6`
  - Logo: `font-interface text-sm font-semibold text-text-intense`
  - Breadcrumb (page-specific text): `font-interface text-xs text-text-muted`

### ReviewPage layout (`/review/:sessionId`)

Narrow column — abstract reading requires comfortable line length.

```
max-w-3xl mx-auto px-6 py-8 flex flex-col gap-6
├── PaperHeader (title + condition badge)
├── AnnotatedAbstract            ← abstract content area
├── SelectionFloater             ← portal, no layout footprint
└── DetectionList                ← flagged items + submit
    [OR CompletionBanner if session.status === 'completed']
```

### ResultsPage layout (`/results/:experimentId`)

Wider to accommodate 4-column table.

```
max-w-5xl mx-auto px-6 py-8 flex flex-col gap-8
├── UpliftHero                  ← centered hero metric
└── ConditionResultsTable       ← includes category breakdown
```

Dev port: `5174` (`server: { port: 5174 }` in `vite.config.ts`).

---

## Component Specs

### `AnnotatedAbstract`

- **Hierarchy:**
  ```
  div.font-data.text-sm.leading-relaxed.text-text-default.whitespace-pre-wrap
    [plain spans + annotated spans interspersed]
  ```

- **Layout:** `font-data text-sm leading-relaxed text-text-default whitespace-pre-wrap bg-surface rounded-lg border border-border p-6`

- **Segmentation algorithm:**
  1. Filter out annotations where `abstract.toLowerCase().indexOf(ann.text_excerpt.toLowerCase()) === -1`.
  2. Sort remaining by `indexOf` result ascending.
  3. Walk through abstract: track `pos = 0`, `coveredUntil = 0`.
  4. For each annotation: `idx = abstract.toLowerCase().indexOf(ann.text_excerpt.toLowerCase(), pos)`. If `idx < coveredUntil`, skip. Push plain `abstract.slice(pos, idx)`. Push highlighted segment `{text: abstract.slice(idx, idx + ann.text_excerpt.length), annotation}`. Set `pos = idx + ann.text_excerpt.length`; `coveredUntil = pos`.
  5. Push final plain segment `abstract.slice(pos)`.

- **Tokens — highlighted span:**
  ```
  <span className="relative group inline">
    <span className={highlightClass}>
      {text}
    </span>
    <span className="absolute bottom-full left-0 z-10 mb-1 hidden group-hover:block
      bg-slate-800 text-slate-50 text-xs rounded px-2 py-1.5 max-w-xs whitespace-normal
      shadow-lg pointer-events-none">
      <span className={confidenceBadgeClass}>{confidence}</span>
      {" "}{reason}
    </span>
  </span>
  ```

  Highlight backgrounds by confidence:
  - `high`: `bg-amber-200 text-amber-900 cursor-help rounded px-0.5`
  - `medium`: `bg-yellow-100 text-yellow-800 cursor-help rounded px-0.5`
  - `low`: `bg-slate-100 text-slate-600 cursor-help rounded px-0.5`

  Confidence badge inside tooltip:
  - `high`: `inline-block bg-amber-500 text-white text-xs px-1 rounded`
  - `medium`: `inline-block bg-yellow-400 text-yellow-900 text-xs px-1 rounded`
  - `low`: `inline-block bg-slate-400 text-white text-xs px-1 rounded`

- **States:**
  - No annotations (unaided condition): renders abstract as a single plain `<span>`. No visual difference from plain text.
  - Empty abstract (should not occur): renders nothing.

- **Data:**
  ```ts
  type AnnotatedAbstractProps = {
    abstract: string
    annotations: Annotation[]  // [] for unaided sessions
  }
  ```

---

### `SelectionFloater`

- **Hierarchy:** Rendered via `createPortal(button, document.body)`. No DOM footprint in the ReviewPage component tree.

- **Behaviour:**
  - `ReviewPage` attaches `onMouseUp={handleMouseUp}` to a wrapper `div` containing the `AnnotatedAbstract`.
  - `handleMouseUp`:
    ```ts
    const sel = window.getSelection()
    const text = sel?.toString().trim() ?? ''
    if (text.length >= 15) {
      const rect = sel!.getRangeAt(0).getBoundingClientRect()
      setFloaterPos({ top: rect.bottom + 8, left: rect.left })
      setPendingExcerpt(text)
    } else {
      setFloaterPos(null)
      setPendingExcerpt(null)
    }
    ```
  - State lives in `ReviewPage`: `floaterPos: { top: number; left: number } | null`, `pendingExcerpt: string | null`.
  - Clicking the button: calls `onFlag(pendingExcerpt)`, then `window.getSelection()?.removeAllRanges()`, then `setFloaterPos(null)`.
  - Dismiss: `onMouseDown` outside the button clears state (use a `useEffect` listening for `mousedown` on `document`).

- **Tokens:**
  ```
  style={{ position: 'fixed', top: floaterPos.top, left: floaterPos.left }}
  className="bg-accent text-white font-interface text-sm px-3 py-1.5 rounded shadow-lg z-50
             hover:bg-blue-700 transition-colors cursor-pointer"
  ```
  Note: `style` prop is required for dynamic coordinates — explicit exception to no-inline-style (Constraints §1).

- **States:**
  - Visible: `floaterPos !== null && pendingExcerpt !== null`
  - Hidden: renders `null`

- **Data:**
  ```ts
  type SelectionFloaterProps = {
    floaterPos: { top: number; left: number } | null
    pendingExcerpt: string | null
    onFlag: (excerpt: string) => void
  }
  ```

---

### `DetectionList`

- **Hierarchy:**
  ```
  div.flex.flex-col.gap-4
  ├── h3.font-interface.text-sm.font-semibold.text-text-intense  "Flagged errors"
  ├── [if detections.length === 0]:
  │     p.font-interface.text-sm.text-text-muted.italic
  │       "No errors flagged yet — select text above to flag."
  ├── [if detections.length > 0]:
  │     ul.flex.flex-col.gap-2
  │       li × N: DetectionItem
  └── div.pt-4.border-t.border-border.flex.flex-col.gap-2
        p.font-interface.text-xs.text-text-muted
          "Submitting with no flags means you found nothing suspicious."
        button[submit]
  ```

- **`DetectionItem` layout:**
  ```
  div.flex.items-start.gap-3.p-3.bg-surface.rounded.border.border-border
  ├── div.flex-1.flex.flex-col.gap-1.min-w-0
  │   ├── span.font-data.text-xs.text-text-intense.break-all.block
  │   │     "{excerpt.length > 60 ? excerpt.slice(0, 60) + '…' : excerpt}"
  │   └── input[type=text].w-full.font-interface.text-xs.bg-transparent.border-0
  │         .border-b.border-border.pb-0.5.text-text-default
  │         .placeholder-text-muted.focus:outline-none.focus:border-accent
  │         placeholder="Add note (optional)"
  └── button.text-text-muted.hover:text-danger.transition-colors.shrink-0
        aria-label="Remove"
        "×"  (font-data text-base)
  ```

- **Submit button tokens:**
  ```
  px-4 py-2 bg-accent text-white font-interface text-sm rounded
  hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors
  ```
  Label: "Submit" when idle; `div.w-4.h-4.rounded-full.border-2.border-white.border-t-transparent.animate-spin` when in-flight.

- **States:**
  - Empty: empty state message (not a blank div)
  - Has items: list renders
  - Submitting: submit button shows spinner, is `disabled`

- **Data:**
  ```ts
  type DetectionListProps = {
    detections: DetectionIn[]
    onAdd: (excerpt: string) => void       // called by SelectionFloater via ReviewPage
    onRemove: (index: number) => void
    onNoteChange: (index: number, note: string) => void
    onSubmit: () => void
    submitting: boolean
  }
  ```
  State managed in `ReviewPage`. `DetectionList` is presentational.

---

### `UpliftHero`

- **Hierarchy:**
  ```
  div.flex.flex-col.items-center.py-10.gap-3
  ├── span.font-interface.text-xs.text-text-muted.uppercase.tracking-widest  "Human Uplift"
  ├── [uplift === null]:
  │     p.font-interface.text-xl.font-medium.text-text-muted  "Results incomplete"
  │     p.font-interface.text-xs.text-text-muted  "Review all conditions to see uplift"
  └── [uplift !== null]:
        p.font-data.text-5xl.font-bold.[colorClass]  formatUplift(uplift)
        p.font-interface.text-xs.text-text-muted.mt-1
          "TPR(human+agent) − TPR(unaided)"
  ```

- **Layout:** `flex flex-col items-center py-10 gap-3`

- **Tokens:**
  - `uplift > 0`: `text-success` (emerald-600)
  - `uplift < 0`: `text-danger` (red-600)
  - `uplift === 0`: `text-text-muted`
  - `uplift === null`: `text-text-muted`, smaller size (`text-xl`)

- **Format function:**
  ```ts
  function formatUplift(uplift: number): string {
    const pct = (uplift * 100).toFixed(1)
    return uplift >= 0 ? `+${pct}%` : `${pct}%`
  }
  ```

- **States:**
  - Loading: `div.flex.flex-col.items-center.py-10.gap-3`: `Skeleton(h-4 w-24)` + `Skeleton(h-14 w-32)` + `Skeleton(h-4 w-48)`
  - Error: `p.font-interface.text-sm.text-danger  "Could not load results — check API"`

- **Data:**
  ```ts
  type UpliftHeroProps = { uplift: number | null }
  ```

---

### `ConditionResultsTable`

- **Hierarchy:**
  ```
  div.flex.flex-col.gap-0
  ├── section (main metrics table)
  │   ├── h2.font-interface.text-base.font-semibold.text-text-intense.mb-4
  │   │     "Detection Rates by Condition"
  │   └── div.overflow-x-auto.rounded-lg.border.border-border
  │         table.w-full.text-sm.bg-surface
  │           thead: tr (4 th)
  │           tbody:
  │             tr (True Positive Rate)
  │             tr (False Positive Rate)
  │             tr (Sessions)
  │
  └── section.border-t.border-border.pt-8.mt-2 (category breakdown)
      ├── h3.font-interface.text-sm.font-medium.text-text-muted.mb-4
      │     "By Error Category"
      └── div.overflow-x-auto.rounded-lg.border.border-border
            table.w-full.text-sm.bg-surface
              thead: tr (4 th)
              tbody: tr × N (one per category)
  ```

- **Table token conventions:**
  - `th`: `font-interface text-xs text-text-muted uppercase tracking-wide text-left px-4 py-3 border-b border-border bg-slate-50`
  - `td` default: `font-data text-sm text-text-intense px-4 py-3 border-b border-border last:border-0`
  - Row label `td` (first column, e.g. "True Positive Rate"): `font-interface text-xs text-text-muted px-4 py-3 border-b border-border`
  - Incomplete cell value: `text-text-muted` with `"—"` content
  - `human_agent` TPR cell when `uplift > 0`: add `bg-emerald-50 text-success font-semibold`
  - `human_agent` TPR cell when `uplift < 0`: add `bg-rose-50 text-danger font-semibold`
  - `human_agent` TPR cell when `uplift === null`: default (no highlight)

- **Value formatting:**
  - TPR/FPR: `condition.true_positive_rate !== null ? (condition.true_positive_rate * 100).toFixed(1) + '%' : '—'`
  - Sessions: `condition.true_positive_rate !== null ? `${condition.sessions_complete} / ${condition.sessions_total}` : `0 / ${condition.sessions_total}``

- **Column order:** Unaided | Agent Only | Human + Agent (matches `Condition` enum order)

- **Category breakdown:** Rows = error categories from `conditions[0].by_category` (any condition). Category label in first column (formatted: `inverted_conclusion` → "Inverted Conclusion"). Subsequent columns = TPR per condition, formatted same as main table. If a condition has no `by_category` entry for that category (missing), render "—".

- **States:**
  - Loading: `div.animate-pulse.space-y-2`: `Skeleton(h-8 w-full)` × 4
  - Any condition incomplete: that condition's cells render "—"; table still renders (not blocked)

- **Data:**
  ```ts
  type ConditionResultsTableProps = {
    results: ExperimentResults
  }
  ```

---

## Supplementary Component Specs

### `PaperHeader` (ReviewPage only)

```
div.flex.flex-col.gap-2
├── div.flex.items-center.gap-2.flex-wrap
│   ├── span (condition badge)
│   └── span.font-interface.text-xs.text-text-muted  "{arxiv_id}"
└── h1.font-interface.text-lg.font-semibold.text-text-intense.leading-snug
      {paper_title}
```

Condition badge tokens:
- `unaided`: `bg-slate-100 text-slate-600 font-interface text-xs px-2 py-0.5 rounded`
- `agent_only`: `bg-accent-subtle text-accent font-interface text-xs px-2 py-0.5 rounded`
- `human_agent`: `bg-amber-50 text-amber-700 font-interface text-xs px-2 py-0.5 rounded`

### `CompletionBanner` (ReviewPage — completed session state)

```
div.rounded-lg.border.border-border.bg-slate-50.p-4.flex.items-center.gap-3
├── span.text-success  "✓"  (font-data text-lg)
└── p.font-interface.text-sm.text-text-default  "Session submitted. Results are being compiled."
```

Renders in place of `DetectionList` when `session.status === 'completed'`.

---

## Hook Specs

```typescript
// src/hooks/useSession.ts
function useSession(id: number | null): UseQueryResult<Session>
// GET /sessions/{id}; enabled: id !== null; refetchInterval: false (session state is set once)

// src/hooks/useSubmitReview.ts
function useSubmitReview(): UseMutationResult<ReviewConfirmOut, Error, ReviewSubmitBody>
// POST /reviews; body: { session_id, detections }
// onSuccess: navigate to /results/{session.experiment_id}

// src/hooks/useResults.ts
function useResults(experimentId: number | null): UseQueryResult<ExperimentResults>
// GET /results/{experimentId}; enabled: experimentId !== null
// refetchInterval: (query) => query.state.data?.uplift === null ? 30_000 : false

// src/hooks/useExperiments.ts
function useExperiments(): UseQueryResult<ExperimentSummary[]>
// GET /experiments; used by any experiment listing view (not strictly required for v1 UI)

// src/hooks/usePapers.ts
function usePapers(params?: { q?: string }): UseQueryResult<PapersPage>
// GET /papers?q=&limit=20; not used in v1 UI (papers managed via CLI)
```

---

## Constraints Applied

1. **`style` prop exception for `SelectionFloater`:** `position: fixed` with computed `top`/`left` from `getBoundingClientRect()` requires the React `style` prop. This is dynamic computed layout — not an arbitrary hardcoded pixel value. The ban in `design_style.md` targets hardcoded `style=""` overrides like `style="margin-left: 13px"`. This usage is correct and unavoidable for a floating element anchored to a text selection.

2. **`whitespace-pre-wrap` for abstract text:** arXiv abstracts contain intentional newlines. Using `whitespace-pre-wrap` preserves the original line breaks without displaying them as visual noise. This is a reading-comfort decision, not a layout deviation.

3. **`group-hover:block` for annotation tooltips:** The `group`/`group-hover` pattern produces `position: absolute` tooltip positioning. This is the correct Tailwind approach — no arbitrary pixel values involved. The `z-10` ensures the tooltip renders above the abstract text.

4. **Emerald-50 / rose-50 as named Tailwind palette classes:** The highlighted TPR cell uses `bg-emerald-50` and `bg-rose-50`. These are not mapped to semantic tokens in the `tailwind.config.js`. They are used for a specific data-state highlight (not general UI state), making them acceptable named palette references rather than semantic token violations — consistent with the `SourceBadge` categorical-color precedent in other projects.

5. **`rounded-lg border border-border` on tables:** Design style prefers "subtle background tint shifts over thick solid borders." Tables use a single outer `border border-border` with `rounded-lg` — this provides structure without heavy lines. Row separators use `border-b border-border` (slate-200) which is the Muted Boundary token — not a harsh decorative border.

---

## Open Questions

1. **`paper_title` in `SessionOut`:** The architect spec notes this field must be added to `SessionOut` (via a join in the sessions router). The implementer must verify this field is present in the API response before wiring `PaperHeader`. If not present, fetch via `GET /papers/{paper_id}` as a separate query in `ReviewPage`.

2. **Navigation from session creation to ReviewPage:** In v1, review sessions are created via `POST /sessions`. There is no UI for creating sessions — this is CLI or API-level setup. `ReviewPage` is navigated to directly by ID. If a "start session" UI is needed, scope it as a v2 addition.

3. **`useExperiments`/`usePapers` hooks:** Defined in spec but not used by v1 UI pages. Implementer may stub them (export the hook, no component uses it) or omit entirely. Include in MSW handlers to avoid future 404 noise.

---

## Handoff

The implementer (phase 6b — frontend) reads this file alongside `roles/architect/output/output.md` and `roles/implementer/output/backend-output.md`.

Deviations from this spec must be documented in `roles/implementer/output/output.md` with a reason.

**Implementation sequence:**
1. `web/` scaffold via `setup-ts-pnpm.md` — `pnpm create vite`, install deps, write `tailwind.config.js` from Token Layer above
2. `src/types/index.ts` — all types from architect output
3. `src/api/client.ts` — `apiFetch` wrapper
4. Hooks: `useSession`, `useSubmitReview`, `useResults`
5. Shared components (dependency order): `AnnotatedAbstract` → `SelectionFloater` → `DetectionList` → `UpliftHero` → `ConditionResultsTable` → `PaperHeader` → `CompletionBanner`
6. Pages: `ReviewPage` → `ResultsPage`
7. `App.tsx` — `BrowserRouter` + two routes + minimal header shell
8. `src/test/handlers.ts` — MSW handlers for all endpoints
9. `ReviewPage.test.tsx` + `ResultsPage.test.tsx` — per done criteria
10. `pnpm build` — must exit 0 with 0 TypeScript errors
