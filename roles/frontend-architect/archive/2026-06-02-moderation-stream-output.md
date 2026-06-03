# Frontend-Architect Output — moderation-stream `/stream` dashboard

**Role:** frontend-architect
**Sequence:** `new-project-full` (step 5)
**Date:** 2026-06-02

---

## Token Layer

The case-queue frontend uses the shadcn/ui CSS-variable token system (`hsl(var(--token))`).
This is an **extension** — the existing token layer is inherited. Two additions required:

### Addition 1 — Monospace font family (`tailwind.config.js`)

```js
// Add to theme.extend:
fontFamily: {
  data: ['JetBrains Mono', 'SF Mono', 'Geist Mono', 'monospace'],
},
```

All metric values (accuracy %, latency ms, throughput cps, total processed) must use `font-data`. No other component in case-queue currently uses this family — it is new.

### Addition 2 — Status active color tokens (`index.css` + `tailwind.config.js`)

The `status-active` (emerald) state has no token in the current shadcn/ui config. Add to `index.css` `:root`:

```css
--status-active-bg: 142.1 76.2% 90%;    /* emerald-100 equivalent */
--status-active-text: 142.1 70.1% 25%;  /* emerald-800 equivalent */
```

And register in `tailwind.config.js` `theme.extend.colors`:

```js
'status-active-bg':   'hsl(var(--status-active-bg))',
'status-active-text': 'hsl(var(--status-active-text))',
```

`pending_weights` status reuses existing shadcn/ui tokens: `bg-muted text-muted-foreground`. No new token needed.

### Existing tokens used by new components

| Token class | CSS variable | Role |
|---|---|---|
| `bg-card` | `--card` | Card background (active) |
| `bg-muted` | `--muted` | Card background (pending) |
| `text-foreground` | `--foreground` | Model name, metric values |
| `text-muted-foreground` | `--muted-foreground` | Metric labels, pending text |
| `border-border` | `--border` | Card border |
| `bg-status-active-bg` | `--status-active-bg` | Active badge background |
| `text-status-active-text` | `--status-active-text` | Active badge text |

---

## Page Layout

**Route:** `/stream`
**Context:** Application Dashboard — high data density, operational monitoring

```
StreamDashboard                        full viewport width, bg-background
├── Page header                        px-6 py-5, border-b border-border
│   ├── h1: "Model Comparison"         text-xl font-semibold text-foreground font-interface
│   └── generated_at timestamp         text-sm text-muted-foreground font-data
├── ErrorMessage (conditional)         px-6 pt-6 — renders when API unreachable
└── Metrics grid                       px-6 py-6
    └── grid grid-cols-1               1 col < md
        md:grid-cols-2                 2 col ≥ md
        xl:grid-cols-3                 3 col ≥ xl
        gap-4
```

**5-card layout in a 3-col grid:** Row 1 = cards 1–3, Row 2 = cards 4–5 (left-aligned naturally). No special CSS needed — CSS Grid left-aligns partial rows by default. Do not use `col-span` tricks or stretching.

**Loading state (first fetch):** Render 5 `<Skeleton>` blocks inside the same grid structure, each the same height as an active card (`h-48`). Use shadcn/ui `Skeleton` component. Removes once `data` is defined. Not shown after first load (subsequent refetches are silent).

---

## Component Specs

### `ModelMetricsCard`

**Hierarchy:**
```
ModelMetricsCard({ metrics: ModelMetrics })
└── Card (shadcn/ui)
    ├── CardHeader
    │   ├── div.flex.items-center.justify-between
    │   │   ├── CardTitle — model name
    │   │   └── StatusBadge — inline, right-aligned
    ├── CardContent  [active state only]
    │   ├── MetricRow × 3  (accuracy / latency / throughput)
    │   └── div — total processed (muted footer line)
    └── CardContent  [pending state only]
        └── p — placeholder message
```

**Layout:**
- Card: no explicit width — fills grid cell. `p-0` on Card, let CardHeader/CardContent handle internal padding.
- CardHeader: `pb-3`
- CardContent: `pt-0`
- MetricRow: `flex items-baseline justify-between` with `py-1`

**Token mapping:**
- Card (active): `bg-card border border-border rounded-lg`
- Card (pending): `bg-muted border border-border rounded-lg`
- CardTitle: `text-sm font-medium text-foreground font-interface`
- Metric label: `text-xs text-muted-foreground font-interface`
- Metric value: `text-sm text-foreground font-data tabular-nums`
- Null accuracy: value renders as `"N/A"` with class `text-muted-foreground font-data`
- Total processed label+value: `text-xs text-muted-foreground font-data tabular-nums` — visually lighter than primary metrics
- Pending placeholder text: `text-sm text-muted-foreground font-interface italic` — centered

**States:**

| State | Trigger | Visual |
|---|---|---|
| Active — data present | `status === 'active'` and metrics loaded | Full metrics panel, full contrast |
| Active — zero data | `status === 'active'` and `total_processed === 0` | Metrics show `0` / `0.0` / `N/A`; no special treatment |
| Pending weights | `status === 'pending_weights'` | Muted card, placeholder text, no metrics rows |
| Loading (initial) | `isLoading && !data` | Skeleton (handled at StreamDashboard level, not inside card) |

**Data:**
```typescript
type ModelMetricsCardProps = {
  metrics: ModelMetrics  // from src/types/stream.ts
}
```

**Metric rows (active state):**

| Row label | Value | Format |
|---|---|---|
| Accuracy | `metrics.accuracy` | `null` → `"N/A"` / number → `"XX.X%"` (`(v * 100).toFixed(1) + '%'`) |
| p50 latency | `metrics.p50_latency_ms` | `"XX.Xms"` |
| p95 latency | `metrics.p95_latency_ms` | `"XX.Xms"` |
| Throughput | `metrics.throughput_cps` | `"X.XX /s"` |
| Total processed | `metrics.total_processed` | integer, no decimals |

---

### `StatusBadge` (inline inside ModelMetricsCard)

Not a standalone component — implemented as a conditional `<span>` or shadcn/ui `<Badge>` inside `ModelMetricsCard`. Do not create a separate file for two CSS classes.

```typescript
// Inside ModelMetricsCard:
const badgeClass = metrics.status === 'active'
  ? 'bg-status-active-bg text-status-active-text'
  : 'bg-muted text-muted-foreground'

const badgeLabel = metrics.status === 'active' ? 'Active' : 'Pending Weights'

// Render as shadcn/ui Badge with className override:
<Badge className={badgeClass}>{badgeLabel}</Badge>
```

Badge sizing: shadcn/ui default (`text-xs px-2 py-0.5`). No custom sizing.

---

### Metrics Grid

Not a standalone component — implemented as a `<div>` with grid classes directly in `StreamDashboard`. Do not extract a `MetricsGrid` component for a static className wrapper.

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
  {data.models.map(m => (
    <ModelMetricsCard key={m.model_name} metrics={m} />
  ))}
</div>
```

---

### Stream Connection Indicator

Not a standalone component. Implemented as two elements in the `StreamDashboard` header:

1. **Normal state** — `generated_at` timestamp rendered as:
   ```tsx
   <p className="text-sm text-muted-foreground font-data">
     Updated {formatRelative(new Date(data.generated_at))}
   </p>
   ```
   Use `date-fns` `formatDistanceToNow` (already likely in project deps; if not, format manually as `new Date(data.generated_at).toLocaleTimeString()`).

2. **Error state** — `ErrorMessage` component replaces the grid entirely:
   ```tsx
   {error && <ErrorMessage message="Could not connect to stream metrics API" />}
   ```
   `ErrorMessage` is the existing component from `src/components/ErrorMessage.tsx`.

---

### Nav Link

Add to the existing top navigation in `App.tsx` or the nav component. Follow the identical pattern as the existing "Cases" and "Audit Log" links.

```tsx
<NavLink to="/stream">Stream</NavLink>
```

No new nav component. No layout change. The label is "Stream" — concise, matches the route name.

---

## Constraints Applied

These `design_style.md` rules are the most constraining for this component set:

1. **No raw hue values.** `emerald-100` / `emerald-800` must not appear in component code — they are only in CSS variables in `index.css`. The component uses `bg-status-active-bg text-status-active-text`. This is enforced by registering the tokens in `tailwind.config.js`.

2. **Monospace for all data.** Every numeric metric value uses `font-data`. The label beside it (e.g. "Accuracy") uses `font-interface`. Mixing these in the same text node is banned — split label and value into separate elements.

3. **No arbitrary pixel values.** Spacing uses the Tailwind 4px scale only. If any MetricRow spacing feels wrong at a Tailwind step, pick the nearest step — do not reach for `gap-[5px]`.

4. **Subtle contrast over heavy borders.** The pending card uses `bg-muted` (tinted background) to differentiate from active cards, not a thick coloured border. The border on all cards is `border-border` (low contrast, uniform).

5. **60/30/10 rule.** Emerald appears only on the status badge — ≤10% of card surface. The rest is neutral slate tones. Do not add colour anywhere else on the card (no coloured metric values, no coloured row backgrounds).

---

## Open Questions

None. The design-brief's four open decisions are resolved above:

| Decision | Resolution |
|---|---|
| Badge token mapping | `--status-active-bg` / `--status-active-text` CSS vars; `bg-muted text-muted-foreground` for pending |
| Card wrapper approach | shadcn/ui `Card` directly — no thin wrapper |
| Loading state | 5 `<Skeleton>` blocks in the grid (initial load only) |
| Timestamp placement | Dashboard header, not per-card footer |

---

## Handoff

**Next role:** implementer
**What the implementer does with this output:**
1. Add `fontFamily.data` to `tailwind.config.js`
2. Add `--status-active-bg` / `--status-active-text` to `index.css` `:root`
3. Register `status-active-bg` / `status-active-text` in `tailwind.config.js` colors
4. Implement in order: `src/types/stream.ts` → `src/api/stream.ts` → `src/components/ModelMetricsCard.tsx` → `src/pages/StreamDashboard.tsx` → `src/App.tsx` (route + nav link)
5. Check `date-fns` is available; if not, use `toLocaleTimeString()` fallback
6. Run `pnpm build` and `pnpm test` before marking frontend implementation complete

**Flags for implementer:**
- Do not use `emerald-100` or `emerald-800` directly in component code — use the registered token classes only.
- The `font-data` class will not work until `tailwind.config.js` is updated. Do that first.
- `tabular-nums` on metric values prevents layout jitter as numbers change on each poll cycle — include it.
- The `Skeleton` component is from shadcn/ui — confirm it is installed (`src/components/ui/skeleton.tsx`); add it with `npx shadcn@latest add skeleton` if absent.
