# Frontend-Architect Output — llm-safety-monitor (UI Redesign)

**Role:** frontend-architect
**Sequence:** `add-feature` (tab redesign)
**Date:** 2026-06-06

---

## Open Decision Resolutions (from design-brief)

- **TaxonomyTrendChart chart type:** Stacked bar chart. With up to 13 harm categories (most
  sparse at any bucket), stacked bars communicate total flagged volume and per-category
  composition simultaneously. Render only categories that appear in the response — no zero-count
  series. Legend is auto-generated from active category names.

- **ModelPerformanceCard timeseries bucket:** Fixed at `bucket_minutes=60` in the hook. No UI
  control. Adds no portfolio value; keeps the tab layout clean.

- **EscalationCard list management:** Refetch-on-success. After `POST /cases/{id}/decide`
  returns 200, call `queryClient.invalidateQueries(['escalation-queue'])`. Simpler than
  optimistic removal and avoids rollback complexity.

- **HumanReview pagination:** Client-side pagination, page size 20. The API returns the full
  queue; the page component slices it. If the queue regularly exceeds 100 items, move
  pagination to the API layer in a follow-up.

---

## Token Layer

**Carried over from moderation-dashboard.** The `tailwind.config.js` below is identical —
accent hue is Blue. Copy it verbatim into `projects/llm-safety-monitor/web/tailwind.config.js`.

```js
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

## Frontend Types (New — Timeseries Endpoints)

These endpoints were added post-architect. Define in `web/src/types/index.ts` alongside
the architect-specified types. **Implementer: verify field names against actual API responses
before wiring hooks.**

```typescript
// GET /metrics/timeseries?bucket_minutes=60
type MetricsBucket = {
  bucket_start: string    // ISO 8601 timestamp
  f1: number
  precision: number
  recall: number
  sample_count: number
}

type ModelTimeseries = {
  model_name: string
  buckets: MetricsBucket[]
}

type TimeseriesResponse = { models: ModelTimeseries[] }

// GET /metrics/taxonomy/timeseries?bucket_minutes=60
type TaxonomyCategoryCount = {
  category: string        // HarmCategory value
  count: number
}

type TaxonomyBucket = {
  bucket_start: string    // ISO 8601 timestamp
  categories: TaxonomyCategoryCount[]
}

type TaxonomyTimeseriesResponse = { buckets: TaxonomyBucket[] }

// POST /cases/{id}/decide — mutation payload
type DecisionPayload = {
  decision: 'approve' | 'dismiss' | 'escalate'
}

// EscalationEntry — response shape for GET /cases (escalation queue)
// Verify against actual API; likely matches the existing case-queue CaseListItem shape
// enriched with verdicts and escalation_reason.
type EscalationEntry = {
  id: string
  event_id: string
  prompt_text: string
  response_text: string | null
  escalation_reason: EscalationReason | null
  verdicts: VerdictEntry[]
  created_at: string
}

type EscalationQueueResponse = {
  cases: EscalationEntry[]
  total: number
}
```

---

## Page Layout

```
┌──────────────────────────────────────────────────────────┐
│  Header: "LLM Safety Monitor" (left)                     │  h-14 bg-surface border-b border-border
├──────────────────────────────────────────────────────────┤
│  PanelTabBar: 4 tabs flush left                          │  border-b border-border
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Panel content area: max-w-7xl mx-auto px-6 py-6        │  bg-background min-h-screen
│                                                          │
└──────────────────────────────────────────────────────────┘
```

- Global wrapper: `min-h-screen bg-background font-interface`
- Header: `h-14 bg-surface border-b border-border flex items-center px-6`
  - App name: `text-base font-semibold text-text-intense font-interface`
- Content: `max-w-7xl mx-auto px-6 py-6`
- Dev port: 5174 (`server: { port: 5174 }` in `vite.config.ts`)

**Panel layouts per tab:**

| Tab | Layout |
|-----|--------|
| Stream Monitor | Single column feed (`flex flex-col`) |
| Model Performance | 3-column card grid (`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4`) |
| Taxonomy Trends | Full-width chart (`w-full`) |
| Human Review | Single column card stack (`flex flex-col gap-4`) + pagination bar |

---

## Component Specs

### PanelTabBar

- **Hierarchy:** `nav > ul > li > button` — one `button` per tab
- **Layout:** `flex border-b border-border` on `nav`; tabs sit flush, no gaps
- **Tokens:**
  - Active: `border-b-2 border-accent text-text-intense font-medium`
  - Inactive: `text-text-muted hover:text-text-default border-b-2 border-transparent`
  - Item: `px-4 py-3 text-sm font-interface transition-colors`
- **States:** inactive, hover (inactive), active
- **Data:** `activeTab: string`, `onTabChange: (tab: string) => void`; tab list is a
  static constant — 4 tabs in order:
  `'stream-monitor' | 'model-performance' | 'taxonomy-trends' | 'human-review'`

---

### EventFeedItem

- **Hierarchy:**
  ```
  li.flex.flex-col.gap-2.py-4.border-b.border-border.last:border-0
  ├── div.flex.items-center.gap-2.flex-wrap    ← badge row
  │   ├── SourceBadge
  │   └── EscalationReasonBadge (render nothing when reason is null)
  ├── p.font-data.text-sm.text-text-default.break-words    ← prompt_text
  ├── p.font-data.text-xs.text-text-muted.break-words      ← response_text (or "(no response)")
  └── VerdictRow(verdicts)
  ```
- **Layout:** `flex flex-col gap-2 py-4 border-b border-border last:border-0`
- **Tokens:**
  - Prompt: `font-data text-sm text-text-default`
  - Response: `font-data text-xs text-text-muted`
  - "(no response)" label: `font-interface text-xs text-text-muted italic`
- **States:**
  - Default: full render (badge row + texts + VerdictRow)
  - Escalated: `EscalationReasonBadge` visible in badge row
  - No distinct hover state — feed is read-only
- **Data:**
  ```ts
  type EventFeedItemProps = {
    event: RecentEvent
  }
  ```
- **Skeleton:** `li.flex.flex-col.gap-2.py-4.border-b.border-border`
  ```
  div.flex.gap-2: Skeleton(h-5 w-16) + Skeleton(h-5 w-24)
  Skeleton(h-4 w-full)
  Skeleton(h-4 w-3/4)
  div.grid.grid-cols-3.gap-4: Skeleton(h-6 w-20) × 3
  ```
  Render 5 `EventFeedItemSkeleton` rows while loading.

---

### VerdictRow

Shared by `EventFeedItem` and `EscalationCard`. Consumes `VerdictEntry[]` from the
verdicts array; finds each model by `model_name`.

- **Hierarchy:**
  ```
  div.grid.grid-cols-3.gap-4
  ├── div.flex.flex-col.gap-1         ← pair_classifier column
  │   ├── span.font-interface.text-xs.text-text-muted  "Pair"
  │   └── VerdictBadge(predicted_label, type="pair")
  ├── div.flex.flex-col.gap-1         ← prompt_detector column
  │   ├── span.font-interface.text-xs.text-text-muted  "Prompt"
  │   └── VerdictBadge(predicted_label, type="prompt")
  └── div.flex.flex-col.gap-1         ← taxonomy_classifier column
      ├── span.font-interface.text-xs.text-text-muted  "Taxonomy"
      └── div.flex.flex-wrap.gap-1
          ← HarmCategoryChip × N, or "none" text
  ```
- **Layout:** `grid grid-cols-3 gap-4`
- **Tokens — VerdictBadge (inline sub-component):**
  - pair, label=0 (Safe): `bg-success/10 text-success font-data text-xs px-2 py-0.5 rounded`
  - pair, label=1 (Unsafe): `bg-danger/10 text-danger font-data text-xs px-2 py-0.5 rounded`
  - prompt, label=0 (Benign): `bg-border text-text-muted font-data text-xs px-2 py-0.5 rounded`
  - prompt, label=1 (Adversarial): `bg-danger/10 text-danger font-data text-xs px-2 py-0.5 rounded`
- **Tokens — HarmCategoryChip (inline sub-component):**
  - `bg-accent-subtle text-accent font-data text-xs px-2 py-0.5 rounded`
- **Tokens — "none" text:**
  - `font-interface text-xs text-text-muted`
- **States:**
  - VerdictRow renders nothing if `verdicts` array is empty (guard with `if (!verdicts.length) return null`)
  - taxonomy column with `taxonomy_labels = []`: renders "none" (not an empty div)
  - taxonomy column with missing `taxonomy_classifier` verdict (model not yet classified): renders "—" in `text-text-muted`
- **Data:**
  ```ts
  type VerdictRowProps = {
    verdicts: VerdictEntry[]
  }
  ```

---

### SourceBadge

Shared by `EventFeedItem` and `EscalationCard`. Five categorical color variants.
These colors use named Tailwind palette classes (not semantic tokens) — categorical data
distinctions, not UI state. See Constraints Applied §4.

- **Hierarchy:** `span` with conditional class set
- **Tokens per source:**
  - `hh-rlhf`: `bg-blue-100 text-blue-700 font-data text-xs px-2 py-0.5 rounded`
  - `wildguard`: `bg-purple-100 text-purple-700 font-data text-xs px-2 py-0.5 rounded`
  - `advbench`: `bg-danger/10 text-danger font-data text-xs px-2 py-0.5 rounded`
  - `jailbreakbench`: `bg-amber-100 text-amber-700 font-data text-xs px-2 py-0.5 rounded`
  - `live`: `bg-success/10 text-success font-data text-xs px-2 py-0.5 rounded`
- **Data:** `{ source: SourceDataset }`

---

### EscalationReasonBadge

Renders nothing (`return null`) when `reason` is null. Five color variants.
`LOG_ONLY` uses muted styling — it is informational, not actionable.

- **Tokens per reason:**
  - `JAILBREAK`: `bg-danger/10 text-danger font-data text-xs px-2 py-0.5 rounded`
  - `BENIGN_HARMFUL`: `bg-warning/10 text-warning font-data text-xs px-2 py-0.5 rounded`
  - `MODEL_DISAGREEMENT`: `bg-amber-100 text-amber-700 font-data text-xs px-2 py-0.5 rounded`
  - `ADVERSARIAL_PROMPT_FLAGGED`: `bg-purple-100 text-purple-700 font-data text-xs px-2 py-0.5 rounded`
  - `LOG_ONLY`: `bg-border text-text-muted font-data text-xs px-2 py-0.5 rounded`
- **Data:** `{ reason: EscalationReason | null }`

---

### ModelPerformanceCard

One card per classifier (3 cards total in a `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4`).

- **Hierarchy:**
  ```
  article.bg-surface.rounded-lg.border.border-border.p-5.flex.flex-col.gap-4
  ├── header.flex.items-center.justify-between
  │   ├── h3: model name
  │   └── span: sample count
  ├── div.grid.grid-cols-3.gap-4           ← metric row
  │   ├── MetricCell(label="F1", value)
  │   ├── MetricCell(label="Precision", value)
  │   └── MetricCell(label="Recall", value)
  └── div.flex.flex-col.gap-1
      ├── span.font-interface.text-xs.text-text-muted.uppercase.tracking-wide  "F1 over time"
      └── ModelTimeseriesChart(buckets)     ← empty state handled inside
  ```
- **Layout:** `bg-surface rounded-lg border border-border p-5 flex flex-col gap-4`
- **Tokens:**
  - Model name: `font-interface text-sm font-semibold text-text-intense`
  - Sample count: `font-data text-xs text-text-muted`
  - Metric label (inside MetricCell): `font-interface text-xs text-text-muted uppercase tracking-wide`
  - Metric value (inside MetricCell): `font-data text-lg font-medium text-text-intense`
  - Value when null/0: `font-data text-lg text-text-muted` — render `"—"`
- **States:**
  - Loading: replaced by `ModelPerformanceCardSkeleton`:
    ```
    article (same outer classes)
    ├── div.flex.justify-between: Skeleton(h-4 w-32) + Skeleton(h-4 w-20)
    ├── div.grid.grid-cols-3.gap-4: Skeleton(h-10 w-full) × 3
    └── Skeleton(h-32 w-full)
    ```
  - Error: card renders with metric values as `"—"` and `p.text-xs.text-danger` error note below metric row
  - No timeseries data: `ModelTimeseriesChart` renders inline placeholder (see below)
- **Data:**
  ```ts
  type ModelPerformanceCardProps = {
    metrics: ModelMetrics            // from /metrics
    timeseries: ModelTimeseries      // from /metrics/timeseries; matching model_name
  }
  ```

**ModelTimeseriesChart (embedded sub-component):**

```
div.h-32.w-full                        ← fixed height div; ResponsiveContainer fills it
├── [if buckets.length === 0]:
│     div.h-32.flex.items-center.justify-center
│       span.font-interface.text-xs.text-text-muted  "No timeseries data"
└── [if buckets.length > 0]:
      ResponsiveContainer(width="100%", height="100%")
      └── LineChart(data=buckets, margin={top:4, right:4, bottom:4, left:0})
          ├── XAxis(dataKey="bucket_start", tickFormatter=formatBucketTime, tick={fontSize:10})
          ├── YAxis(domain=[0,1], tick={fontSize:10}, tickCount=3)
          ├── Tooltip(formatter=(v) => v.toFixed(3))
          └── Line(dataKey="f1", stroke="#2563eb", dot=false, strokeWidth=1.5)
```

`formatBucketTime`: parses ISO string → `HH:mm` using `Intl.DateTimeFormat`.
recharts `stroke` is a raw hex value — cannot read CSS variables (see Constraints §3).

---

### TaxonomyTrendChart

Full-width chart on the Taxonomy Trends tab. Stacked bar chart.

- **Hierarchy:**
  ```
  div.flex.flex-col.gap-4
  ├── div.flex.items-center.justify-between
  │   ├── h2.font-interface.text-base.font-semibold.text-text-intense  "Harm Category Trends"
  │   └── span.font-interface.text-xs.text-text-muted  "60-min buckets"
  └── [if no data]:
        div.h-64.flex.items-center.justify-center.bg-surface.rounded-lg.border.border-border
          span.font-interface.text-sm.text-text-muted  "No taxonomy data yet"
      [if data]:
        div.h-64.w-full.bg-surface.rounded-lg.border.border-border.p-4
          ResponsiveContainer(width="100%", height="100%")
          └── BarChart(data=pivoted_buckets, margin={top:4,right:4,bottom:24,left:0})
              ├── XAxis(dataKey="bucket_start", tickFormatter=formatBucketTime,
              │         tick={fontSize:10}, angle=-30, textAnchor="end")
              ├── YAxis(tick={fontSize:10})
              ├── Tooltip
              ├── Legend(wrapperStyle={fontSize:10})
              └── Bar × N  (one per active category, stackId="a")
  ```
- **Layout:** `flex flex-col gap-4 w-full`
- **Data pivoting:** The API returns `{ buckets: [{ bucket_start, categories: [{category, count}] }] }`.
  Before passing to recharts, pivot to a flat array where each row is a bucket and each
  category is a key:
  ```ts
  // [{ bucket_start: "...", hate: 3, harassment: 1, violence: 0, ... }, ...]
  type PivotedBucket = { bucket_start: string } & Record<string, number>
  ```
  Collect all distinct category names across all buckets to know which `Bar` components to render.
- **Colors:** Fixed hex palette, one per category slot (recharts cannot use CSS variables):
  ```ts
  const CATEGORY_COLORS = [
    '#2563eb', '#059669', '#f59e0b', '#dc2626', '#7c3aed',
    '#0891b2', '#db2777', '#65a30d', '#ea580c', '#0284c7',
    '#9333ea', '#16a34a', '#d97706',
  ]
  // Map category name → CATEGORY_COLORS[index % 13] using sorted category list for stable assignment
  ```
- **States:**
  - Loading: `div.h-64.animate-pulse.bg-surface.rounded-lg.border.border-border`
  - Empty data: placeholder div (see hierarchy above)
  - Error: parent `TaxonomyTrends` page renders `ErrorMessage` component; chart not rendered
- **Data:**
  ```ts
  type TaxonomyTrendChartProps = {
    data: TaxonomyTimeseriesResponse
  }
  ```

---

### EscalationCard

One card per case in the HumanReview queue. Decision buttons trigger a mutation.

- **Hierarchy:**
  ```
  article.bg-surface.rounded-lg.border.border-border.p-5.flex.flex-col.gap-4
  ├── header.flex.items-center.justify-between.gap-2
  │   ├── EscalationReasonBadge(reason)
  │   └── span.font-data.text-xs.text-text-muted  "{id.slice(-8)}"  ← last 8 chars of id
  ├── div.flex.flex-col.gap-2
  │   ├── p.font-data.text-sm.text-text-default.break-words   prompt_text
  │   └── p.font-data.text-xs.text-text-muted.break-words     response_text | "(no response)"
  ├── VerdictRow(verdicts)
  └── footer.flex.items-center.gap-3.pt-3.border-t.border-border
      ├── button.approve   "Approve"
      ├── button.dismiss   "Dismiss"
      └── button.escalate  "Escalate"
  ```
- **Layout:** `bg-surface rounded-lg border border-border p-5 flex flex-col gap-4`
- **Button tokens:**
  - Approve: `px-3 py-1.5 rounded text-sm font-interface bg-success/10 text-success
    hover:bg-success/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors`
  - Dismiss: `px-3 py-1.5 rounded text-sm font-interface bg-border text-text-muted
    hover:bg-slate-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors`
  - Escalate: `px-3 py-1.5 rounded text-sm font-interface bg-danger/10 text-danger
    hover:bg-danger/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors`
- **States:**
  - Default: all buttons enabled
  - In-flight: all three buttons disabled (`disabled` attribute); clicked button renders
    an inline spinner (a simple `animate-spin` border div, 12px) in place of its label
  - Decided: card removed from view via invalidation + refetch
- **Data:**
  ```ts
  type EscalationCardProps = {
    caseItem: EscalationEntry
    onDecide: (caseId: string, decision: 'approve' | 'dismiss' | 'escalate') => void
    isPending: boolean   // true while mutation is in-flight for this caseId
  }
  ```
- **Skeleton:**
  ```
  article (same outer classes)
  ├── div.flex.justify-between: Skeleton(h-5 w-24) + Skeleton(h-4 w-16)
  ├── Skeleton(h-16 w-full)
  ├── div.grid.grid-cols-3.gap-4: Skeleton(h-6 w-20) × 3
  └── div.flex.gap-3.pt-3.border-t.border-border: Skeleton(h-8 w-20) × 3
  ```

---

## Hook Specs

```typescript
// api/stream.ts — carried over (no changes)
function useRecentEvents(limit = 50): UseQueryResult<StreamResponse>
// refetchInterval: 5000

// api/metrics.ts — updated + new hooks
function useModelMetrics(): UseQueryResult<MetricsResponse>
// refetchInterval: 30000

function useMetricsTimeseries(): UseQueryResult<TimeseriesResponse>
// GET /metrics/timeseries?bucket_minutes=60; refetchInterval: 60000

function useTaxonomyTimeseries(): UseQueryResult<TaxonomyTimeseriesResponse>
// GET /metrics/taxonomy/timeseries?bucket_minutes=60; refetchInterval: 60000

// api/review.ts — updated
function useEscalationQueue(): UseQueryResult<EscalationQueueResponse>
// GET /cases (with escalated=true filter if supported); refetchInterval: 10000

function useDecide(): UseMutationResult<
  void,
  Error,
  { caseId: string; decision: 'approve' | 'dismiss' | 'escalate' }
>
// POST /cases/{caseId}/decide; body: { decision }
// onSuccess: queryClient.invalidateQueries({ queryKey: ['escalation-queue'] })
```

---

## Constraints Applied

1. **No arbitrary px values in recharts wrappers:** recharts `ResponsiveContainer` requires
   its parent `div` to have an explicit height via Tailwind class (`h-32`, `h-64`). Never
   pass a raw pixel value to `ResponsiveContainer`'s `height` prop.

2. **60-30-10 rule with many badge colors:** `SourceBadge`, `EscalationReasonBadge`,
   `VerdictBadge`, and `HarmCategoryChip` all appear simultaneously in `EventFeedItem`.
   Resolution: all badge backgrounds are at low opacity (`/10`) or light tints (`-100`)
   so they read as tinted neutrals. The full accent color is confined to `HarmCategoryChip`
   and the `PanelTabBar` active state only.

3. **recharts stroke cannot use CSS variables:** All `stroke` and `fill` props in recharts
   components use raw hex values (`#2563eb`, etc.). If the accent hue changes, update these
   values in `ModelTimeseriesChart.tsx` and `TaxonomyTrendChart.tsx`. Add a comment in
   each file marking the hardcoded values.

4. **SourceBadge categorical colors exceed semantic token set:** Five dataset sources map to
   five distinct colors; only two (danger=advbench, success=live) align with semantic tokens.
   The others (blue-100/blue-700, purple-100/purple-700, amber-100/amber-700) use named
   Tailwind palette classes directly. This is an explicit exception for categorical data
   distinction — not arbitrary, not hex-coded.

5. **"Subtle contrast over heavy shapes" for stacked cards (HumanReview):** `EscalationCard`
   cards on `bg-background`. Card surface is `bg-surface` (white), providing contrast via
   background tint shift. The `border border-border` (slate-200) is structural, not
   decorative — cards need a visible boundary to separate stacked items.

---

## Open Questions

The following are intentionally left to the implementer:

1. **EscalationQueueResponse shape:** Verify the actual GET /cases response schema against
   the case-queue API or the llm-safety-monitor `/cases` router. The `EscalationEntry` type
   in this spec is a projection — field names may differ. Update the type if needed.

2. **Spinner implementation:** The in-flight button spinner is a simple `animate-spin` border
   div (`w-3 h-3 rounded-full border-2 border-current border-t-transparent`). If shadcn/ui
   has a `Spinner` or `Loader` component already in the project, use that instead.

3. **Relative timestamp for EventFeedItem:** No timestamp is shown in the current spec.
   If the implementer adds one (e.g., "3s ago" below the badge row), use
   `Intl.RelativeTimeFormat` — do not pull in a date library for this alone.

4. **HumanReview empty queue badge:** The tab label can optionally show a count badge
   (e.g., "Human Review (4)") when cases are pending. This is out of scope for this spec
   but easy to wire — `useEscalationQueue().data?.total` is available. Implementer's call.

---

## Handoff

The implementer reads this file alongside `roles/architect/output/output.md`.

Deviations from this spec must be documented in `roles/implementer/output/output.md` with a reason.

**Implementation sequence:**
1. Extend `web/src/types/index.ts` with timeseries types defined in this file.
2. Add new hooks to `api/metrics.ts` and `api/review.ts` per hook specs above.
3. Implement shared components in dependency order:
   `SourceBadge` → `EscalationReasonBadge` → `VerdictRow` → `EventFeedItem` → `EscalationCard`
   → `ModelTimeseriesChart` → `ModelPerformanceCard` → `TaxonomyTrendChart`
4. Update `PanelTabBar` to 4 tabs; remove Calibration and ModelComparison tab entries.
5. Implement pages: `StreamMonitor` (update) → `ModelPerformance` (rework) →
   `TaxonomyTrends` (new) → `HumanReview` (rework).
6. Write vitest tests for each new/updated component covering: loading skeleton, empty state,
   data-populated state, error state. For `EscalationCard`, test button disabled state
   during mutation in-flight.
7. Remove `Calibration.tsx`, `ModelComparison.tsx` and their test files. Remove imports from
   `App.tsx`. Remove `useCalibration()` and `useDisagreements()` hooks if no longer referenced.
