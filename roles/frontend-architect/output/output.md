# Frontend-Architect Output — moderation-dashboard

**Role:** frontend-architect
**Sequence:** `new-project-full` (step 5)
**Date:** 2026-06-03

---

## Open Decision Resolutions (from design-brief)

- **Model Performance vs Model Comparison:** Two separate tabs. Model Performance shows production group (round-robin) metrics; Model Comparison shows shadow group metrics side-by-side. No shared selection state, no cross-tab drill-down. Clean separation of stories.
- **ModelCard grid:** `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4`. Phase 1 (3 active cards) fills the 3-column row exactly. Phase 2 (5 cards) wraps to 3+2 — acceptable; no layout reflow or breakpoint logic needed.
- **Stream Monitor layout:** Same `max-w-7xl` container as all other panels. Internal layout is a 3-row stack (`space-y-6`): stat row → category chart → anomaly feed. No hero treatment.
- **MetricSparkline data source:** Client-side accumulation in React state inside each metrics hook. Up to 30 points per model. Resets on page refresh. A server-side time-series endpoint is deferred — document this limitation in README.

---

## Token Layer

**Accent hue: Blue** — assumed default for operational dashboard register. Change `blue` → any Tailwind hue in `tailwind.config.js` and all components update automatically via semantic tokens.

### `tailwind.config.js`

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

No dark mode tokens in this config — the dashboard is light-mode only for the portfolio build. Dark mode can be added in a follow-up pass by adding `dark:` values.

---

## Page Layout

```
┌──────────────────────────────────────────────────────────┐
│  Header: app name (left) · [no right content]            │  h-14, bg-surface, border-b border-border
├──────────────────────────────────────────────────────────┤
│  PanelTabBar: 5 tabs flush left                          │  border-b border-border
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
- Dev port: 5174 (set `server: { port: 5174 }` in `vite.config.ts`)

---

## Component Specs

### PanelTabBar

- **Hierarchy:** `nav > ul > li > button` — one `button` per tab
- **Layout:** `flex border-b border-border` on `nav`; tabs sit flush, no gaps
- **Tokens:**
  - Active tab: `border-b-2 border-accent text-text-intense font-medium`
  - Inactive tab: `text-text-muted hover:text-text-default border-b-2 border-transparent`
  - Tab item: `px-4 py-3 text-sm font-interface transition-colors`
- **States:**
  - Default (inactive): `text-text-muted`
  - Hover (inactive): `text-text-default`
  - Active: `text-text-intense border-b-2 border-accent`
- **Data:** receives `activeTab: string` and `onTabChange: (tab: string) => void`; tab list is a static constant (no API)
- **Tabs (in order):** `stream-monitor` | `model-performance` | `model-comparison` | `human-review` | `analytics`

---

### ModelCard

- **Hierarchy:**
  ```
  article.bg-surface.rounded-lg.border.border-border.p-5
  ├── header (flex row): model name + StatusBadge
  ├── [active only] MetricGrid (2-col grid of metric pairs)
  │   ├── MetricCell × 4: F1 · Precision · Latency p50 · Latency p95
  │   └── MetricCell × 1 full-width: Throughput
  ├── [active only] MetricSparkline
  └── [pending only] PendingLabel (centered)
  ```
- **Layout:**
  - Card: `bg-surface rounded-lg border border-border p-5 flex flex-col gap-4`
  - Header: `flex items-center justify-between`
  - MetricGrid: `grid grid-cols-2 gap-x-6 gap-y-3`
  - Full-width metric (throughput): `col-span-2`
- **Tokens:**
  - Model name: `font-interface text-sm font-semibold text-text-intense`
  - Metric label: `font-interface text-xs text-text-muted uppercase tracking-wide`
  - Metric value: `font-data text-base font-medium text-text-intense`
  - `null` metric (not enough data yet): `font-data text-base text-text-muted` — render `"—"`
- **States:**
  - **Active:** full card rendered; opacity 100%
  - **Pending weights:** `opacity-60`; no MetricGrid; no MetricSparkline; PendingLabel rendered: `font-interface text-sm text-text-muted text-center py-4` — "Awaiting checkpoint"
  - **Loading:** replaced by `ModelCardSkeleton` — see skeleton spec below
  - **Error:** card renders with metric values as `"—"` and error note at bottom in `text-xs text-danger`
- **StatusBadge sub-component** (used inside ModelCard header):
  - `active`: `bg-success/10 text-success text-xs font-data px-2 py-0.5 rounded-full` — "active"
  - `pending_weights`: `bg-warning/10 text-warning text-xs font-data px-2 py-0.5 rounded-full` — "pending"
- **Data:** `ModelMetrics` from architect `schemas.py`:
  ```ts
  type ModelCardProps = {
    metrics: ModelMetrics
    sparklineData: number[]   // accumulated F1 history, up to 30 points
  }
  ```

---

### MetricSparkline

- **Hierarchy:**
  ```
  div.h-12.w-full          ← provides height for recharts DOM read
  └── ResponsiveContainer(width="100%", height="100%")
      └── LineChart(data, margin={top:2,right:0,bottom:2,left:0})
          └── Line(type="monotone", dataKey="value", stroke=accent, dot=false, strokeWidth=1.5)
  ```
- **Layout:** `div` with `h-12` (48px) wrapping `ResponsiveContainer`. No padding classes on the `div` — recharts fills it fully.
- **Tokens:**
  - Line stroke: `#2563eb` (accent token value) — hardcoded in recharts `stroke` prop since recharts does not read CSS vars. If accent hue changes, update this value in `MetricSparkline.tsx`.
  - No CartesianGrid, no Legend, no Tooltip, no XAxis, no YAxis — fully decorative
- **States:**
  - **< 2 data points:** render `Line` with data `[{value:0},{value:0}]` — flat line at bottom; no empty box
  - **Normal:** standard line over accumulated history
- **Data:** `data: number[]` — each entry is a raw F1 value (0.0–1.0). Component maps to `{value: n}` internally before passing to recharts.

---

### AnomalyFeedItem

- **Hierarchy:**
  ```
  li.flex.items-start.gap-3.py-3.border-b.border-border.last:border-0
  ├── SignalName: span
  ├── ZScoreBadge: span
  └── Timestamp: span.ml-auto
  ```
- **Layout:** `flex items-start gap-3 py-3 border-b border-border last:border-0`
- **Tokens:**
  - Signal name: `font-data text-sm text-text-default`
  - Z-score badge (Z > 3): `font-data text-xs px-2 py-0.5 rounded bg-warning/15 text-warning`
  - Z-score badge (Z ≤ 3): `font-data text-xs px-2 py-0.5 rounded bg-border text-text-muted`
  - Timestamp: `font-interface text-xs text-text-muted ml-auto whitespace-nowrap`
- **States:**
  - No hover state; no interaction; read-only
  - Empty feed: parent renders `font-interface text-sm text-text-muted py-4 text-center` — "No anomalies detected"
- **Data:**
  ```ts
  type AnomalyFeedItemProps = {
    flag: AnomalyFlagRead   // from architect schemas.py
  }
  ```
  Timestamp formatted with `Intl.RelativeTimeFormat` — seconds/minutes/hours ago.

---

### EscalationCaseRow

- **Hierarchy:**
  ```
  a[href={caseQueueUrl}/cases/{id}][target="_blank"][rel="noopener noreferrer"]
  └── li.flex.items-center.gap-4.py-3.border-b.border-border.last:border-0
      ├── ContentExcerpt: span.truncate.flex-1
      ├── CategoryBadge: span
      ├── ReasonBadge: span
      └── ExternalLinkIcon: svg (lucide ExternalLink, 14px)
  ```
- **Layout:** `flex items-center gap-4 py-3 border-b border-border last:border-0`; `ContentExcerpt` gets `flex-1 min-w-0` to allow truncation
- **Tokens:**
  - Content excerpt: `font-interface text-sm text-text-default truncate`
  - Category badge: `font-data text-xs px-2 py-0.5 rounded bg-accent-subtle text-accent`
  - Reason badge — `model_disagreement`: `bg-danger/10 text-danger text-xs font-data px-2 py-0.5 rounded`
  - Reason badge — `low_confidence`: `bg-warning/10 text-warning text-xs font-data px-2 py-0.5 rounded`
  - Link icon: `text-text-muted group-hover:text-accent flex-shrink-0` (wrap `a` in `group` class)
- **States:**
  - Hover: full row background tints to `hover:bg-accent-subtle/50` — subtle highlight on hover since row is a link
  - Empty escalation list: `font-interface text-sm text-text-muted py-4 text-center` — "No pending escalations"
  - **Case queue unreachable:** parent `HumanReview` panel shows `ErrorMessage` component with title "Case queue unavailable" and body "Retrying automatically…"; `EscalationCaseRow` list is not rendered
- **Data:**
  ```ts
  type EscalationCaseRowProps = {
    caseItem: CaseListItem    // from case-queue GET /cases response
    caseQueueUrl: string      // from VITE_CASE_QUEUE_URL
  }
  ```

---

## Skeleton Loading Specs

Used by all panels while data is in-flight. Import `Skeleton` from shadcn/ui.

**ModelCardSkeleton:** same outer card dimensions as `ModelCard`
```
article.bg-surface.rounded-lg.border.border-border.p-5.flex.flex-col.gap-4
├── div.flex.justify-between: Skeleton(h-4 w-32) + Skeleton(h-5 w-16)
├── div.grid.grid-cols-2.gap-x-6.gap-y-3:
│   Skeleton(h-8 w-full) × 4
└── Skeleton(h-12 w-full)
```

**FeedItemSkeleton** (for AnomalyFeed and EscalationList):
```
li.flex.items-center.gap-3.py-3.border-b.border-border:
  Skeleton(h-4 w-28) + Skeleton(h-5 w-12) + Skeleton(h-4 w-16 ml-auto)
```
Render 3 `FeedItemSkeleton` rows while loading.

---

## Hook Data Accumulation Pattern

For sparklines — implement in `useProductionMetrics` and `useShadowMetrics`:

```ts
const MAX_HISTORY = 30

export function useProductionMetrics() {
  const [history, setHistory] = useState<Record<string, number[]>>({})

  const query = useQuery({
    queryKey: ['metrics', 'production'],
    queryFn: () => apiFetch<ModelMetrics[]>('/metrics/production'),
    refetchInterval: 3000,
  })

  useEffect(() => {
    if (!query.data) return
    setHistory(prev => {
      const next = { ...prev }
      for (const m of query.data) {
        const pts = next[m.model_name] ?? []
        next[m.model_name] = [...pts, m.f1 ?? 0].slice(-MAX_HISTORY)
      }
      return next
    })
  }, [query.data])

  return { metrics: query.data, history, isLoading: query.isLoading, isError: query.isError }
}
```

`useShadowMetrics` follows the identical pattern.

---

## Constraints Applied

1. **No arbitrary px values in recharts wrappers:** recharts `ResponsiveContainer` requires an explicit `height`. Resolution: always wrap in a `div` with a Tailwind height class (`h-12`, `h-48`); recharts reads the div's DOM height. This is the correct pattern — never pass `height` as a raw pixel to `ResponsiveContainer`.

2. **60-30-10 rule with multiple state badge colors (success/warning/danger):** Multiple badge types appear simultaneously on Model Performance. Resolution: all badges use `/10` or `/15` opacity backgrounds — they read as tinted neutrals, not full accent blocks. Only `PanelTabBar` active state and category badges use the full `accent` token. State colors (success/warning/danger) are confined to badge backgrounds at low opacity and badge text only.

3. **"Subtle contrast over heavy shapes" for card separation:** Cards sit on `bg-background` (slate-50). `bg-surface` (white) cards provide contrast via background tint shift, not a heavy border. The `border border-border` is `slate-200` — light enough to read as structural, not harsh.

4. **Monospace for all metric values:** Every number that represents a computed metric (F1, latency, throughput, Z-score, event rate, escalation count) must use `font-data`. Category labels, model names, panel titles, and descriptive copy use `font-interface`. No mixing within a single text node.

5. **recharts stroke color cannot use CSS variables:** recharts `stroke` prop is a DOM attribute, not a CSS property, so it cannot read `var(--color-accent)`. Resolution: use the raw hex value of the accent token (`#2563eb`) as the stroke. Comment this in `MetricSparkline.tsx` so the implementer knows to update it if the accent hue changes.

---

## Open Questions

The following decisions are intentionally left to the implementer:

1. **Chart library version:** recharts v2 vs v3 — pick whichever is current stable; no architectural difference for this usage.
2. **Relative timestamp formatting:** `Intl.RelativeTimeFormat` or a library (`date-fns/formatDistanceToNow`) — either is acceptable; no component API difference.
3. **lucide-react icon size:** `14` or `16` for the `ExternalLink` icon in `EscalationCaseRow` — implementer's call based on visual fit at review time.
4. **Analytics chart colour per model:** `ModelAccuracyChart` shows multiple models as separate lines. The implementer should pick a fixed palette of 5 distinct colours (one per model) using Tailwind palette values — no arbitrary hex codes. Suggest: blue-600, emerald-600, amber-500, violet-600, rose-600.

---

## Handoff

The implementer reads this file alongside `roles/architect/output/output.md`.

Deviations from this spec must be documented in `roles/implementer/output/output.md` with a reason.

**Implementation sequence for the frontend:**
1. Write `tailwind.config.js` from the Token Layer section above.
2. Scaffold the React app with `pnpm create vite web --template react-ts` at `projects/moderation-dashboard/web/`. Apply `skills/setup-ts-pnpm.md`.
3. Add shadcn/ui base components needed: `Skeleton`, `Badge`. Do NOT run `npx shadcn init` non-interactively — install shadcn primitives manually or defer to a live terminal session.
4. Implement components in dependency order: `PanelTabBar` → `StatusBadge` → `MetricSparkline` → `ModelCard` → `AnomalyFeedItem` → `EscalationCaseRow`.
5. Implement API hooks with accumulation pattern before wiring into page components.
6. Implement pages: `StreamMonitor` → `ModelPerformance` → `ModelComparison` → `HumanReview` → `Analytics`.
7. Write vitest tests for each page component covering loading, error, and data-populated states.
