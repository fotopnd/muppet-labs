# Architect Output — Red-Team Platform Dashboard Refinement v2

**Role:** architect  
**Sequence:** add-feature  
**Date:** 2026-06-13  
**Reads:** `roles/planner/output/output.md`

---

## Decisions

**D1 — `dedup=true` in `GET /runs`:** Use raw `text()` SQL with `DISTINCT ON (r.attack_id)`. Includes JOIN to attacks table, eliminating the N+1 pattern in the current implementation. `session_id` is required (non-nullable) when `dedup=True` — safe with asyncpg. When `dedup=False`, existing paginated logic unchanged.

**D2 — `POST /bias/back-translate`:** POST with JSON body avoids URL length limits for long response texts. Returns `{ translated: string }`. Uses `claude-haiku-4-5-20251001`. No DB storage. Add `anthropic` to `pyproject.toml` dependencies.

**D3 — `useBackTranslation`:** TanStack Query `useQuery` with `queryKey: ['back-translate', sourceLang, text]` and `staleTime: Infinity`. `enabled: !!text`. Deduplication and caching handled by TanStack Query's internal cache — no extra state needed.

**D4 — `AnalyticsSummary` / `RegressionSummary`:** Both call their own hooks (TanStack Query deduplicates network requests). No props needed. Clean single-responsibility components.

**D5 — `Analytics.tsx` padding:** Remove outer `<div className="p-4">` from `StrategyComparison` and `RegressionTracker`. They are no longer standalone tabs. `Analytics.tsx` controls section padding. Anchor IDs added for jump links.

**D6 — Cluster chart axes:** Recharts `ScatterChart` with numeric X (strategy index) and Y (category index), `tickFormatter` mapping to string names. Strategies and categories sorted by descending total cluster size for those strategy/category groups. Click still works — payload carries the cluster.

**D7 — `strategyDescriptions.ts`:** All 35 strategy keys documented. The `example` field rendered in AttackBrowser detail panel in a `<code>` block. Descriptions 2–3 sentences.

---

## Backend

### `pyproject.toml`
Add `anthropic>=0.40.0` to `dependencies`.

### `api/schemas.py` — additions

```python
class BackTranslateIn(BaseModel):
    text: str
    source_lang: Literal["zh", "ru", "ar"]

class BackTranslateOut(BaseModel):
    translated: str
```

Import `Literal` from `typing`.

### `api/routers/runs.py` — `GET /runs` with `dedup` param

Add `dedup: bool = False` param. When `dedup=True` and `session_id` is provided, use:

```sql
SELECT DISTINCT ON (r.attack_id)
    r.id,
    r.session_id,
    r.attack_id,
    r.model_name,
    r.response_text,
    r.jailbreak_success,
    r.classifier_score,
    r.latency_ms,
    r.created_at,
    a.harm_category,
    a.strategy,
    a.attack_text
FROM runs r
JOIN attacks a ON a.id = r.attack_id
WHERE r.session_id = :session_id
ORDER BY r.attack_id, r.created_at DESC
```

Map each row from `result.mappings()` to `RunOut`. Return total as `len(items)` (no separate count query needed in dedup mode). Page/page_size params are ignored when `dedup=True`.

When `dedup=False`: existing paginated logic unchanged (N+1 not fixed; leave it).

Raise `HTTPException(400, "session_id required when dedup=True")` if `dedup=True` and `session_id=None`.

### `api/routers/bias.py` — `POST /bias/back-translate`

```python
@router.post("/bias/back-translate", response_model=BackTranslateOut)
async def back_translate(body: BackTranslateIn) -> BackTranslateOut:
    import anthropic
    client = anthropic.Anthropic()
    lang_names = {"zh": "Chinese", "ru": "Russian", "ar": "Arabic"}
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": (
                f"Translate the following {lang_names[body.source_lang]} text to English. "
                f"Return only the translation, no explanation:\n\n{body.text}"
            ),
        }],
    )
    translated = msg.content[0].text if msg.content else ""
    return BackTranslateOut(translated=translated)
```

Note: `anthropic.Anthropic()` reads `ANTHROPIC_API_KEY` from env automatically. Import is deferred inside the function (per python-conventions.md slow-import rule).

---

## Frontend

### `src/lib/strategyDescriptions.ts` — full 35-entry map

All 35 strategy keys with `label`, `description` (2–3 sentences), `example`.

Grouped entries by mechanism (all must be present):

| Key | Label |
|-----|-------|
| `AIM` | AIM — Always Intelligent & Machiavellian |
| `autodan` | AutoDAN |
| `base64` | Base64 (full prompt) |
| `base64_input_only` | Base64 (input only) |
| `base64_output_only` | Base64 (output only) |
| `base64_raw` | Base64 Raw |
| `combination_1` | Combination Attack 1 |
| `combination_2` | Combination Attack 2 |
| `combination_3` | Combination Attack 3 |
| `dev_mode_v2` | Developer Mode v2 |
| `disemvowel` | Disemvowel |
| `distractors` | Distractors |
| `distractors_negated` | Distractors (Negated) |
| `evil_confidant` | Evil Confidant |
| `evil_system_prompt` | Evil System Prompt |
| `few_shot_json` | Few-Shot JSON |
| `gcg` | GCG (Greedy Coordinate Gradient) |
| `leetspeak` | Leetspeak |
| `low_resource` | Low-Resource Language |
| `low_resource_english` | Low-Resource English |
| `multi_shot_5` | Multi-Shot (5 examples) |
| `multi_shot_25` | Multi-Shot (25 examples) |
| `none` | No Jailbreak (Baseline) |
| `obfuscation` | Obfuscation |
| `original_prompt` | Original Prompt |
| `poems` | Poem Framing |
| `prefix_injection` | Prefix Injection |
| `prefix_injection_hello` | Prefix Injection (Hello) |
| `refusal_suppression` | Refusal Suppression |
| `refusal_suppression_inv` | Refusal Suppression (Inverted) |
| `rot13` | ROT-13 |
| `style_injection_json` | Style Injection (JSON) |
| `style_injection_short` | Style Injection (Short) |
| `wikipedia` | Wikipedia Framing |
| `wikipedia_with_title` | Wikipedia Framing (with Title) |

### `src/App.tsx` — nav changes

Remove tabs: "Coverage", "Strategy", "Regression"  
Add tab: "Analytics" → `<Analytics />`  

Final tab order: Attack Browser | Analytics | Sample Review | Failure Clusters | Bias Heatmap

### `src/pages/Analytics.tsx` — new file

```tsx
export function Analytics() {
  return (
    <div>
      <div id="strategy" className="p-4">
        <h2 className="text-base font-semibold text-text-primary mb-1">Strategy Performance</h2>
        <p className="text-xs text-text-muted mb-4">
          How each attack strategy performs against the model — success rate, volume, and category coverage.
        </p>
        <StrategyComparison />
      </div>

      <hr className="border-border mx-4" />

      <div id="regression" className="p-4 mt-2">
        <h2 className="text-base font-semibold text-text-primary mb-1">Regression Tracking</h2>
        <p className="text-xs text-text-muted mb-4">
          Attack success rate across sessions — track whether model safety is improving or regressing.
        </p>
        <RegressionTracker />
      </div>
    </div>
  )
}
```

Jump links at top of Analytics (inside top `<div id="strategy">`, before h2):
```tsx
<div className="flex gap-3 text-xs mb-4">
  <a href="#strategy" className="text-accent hover:underline">↓ Strategy</a>
  <a href="#regression" className="text-accent hover:underline">↓ Regression</a>
</div>
```

### `src/pages/StrategyComparison.tsx` — changes

1. Remove outer `<div className="p-4">` — Analytics controls padding
2. Remove `<h2>Strategy Comparison</h2>` heading — Analytics provides it
3. ASR bar: add `<Cell>` per bar with threshold fill:
   - `asr_pct < 30` → `#22c55e` (green)
   - `asr_pct >= 30 && < 60` → `#f59e0b` (amber)
   - `asr_pct >= 60` → `#ef4444` (red)
4. After the 3 panels: `<AnalyticsSummary />`

### `src/pages/RegressionTracker.tsx` — changes

1. Remove outer `<div className="p-4">` — Analytics controls padding
2. Remove `<h2>Regression Tracker</h2>` heading — Analytics provides it
3. After the 4 panels: `<RegressionSummary model={resolvedModel} />`

### `src/components/AnalyticsSummary.tsx` — new file

Props: none. Calls `useStrategyComparison()` and `useCoverage()` directly.

Computed statements:
```
const best = bars sorted by asr desc [0]
const worst = bars sorted by asr asc [0] (exclude 'none'/'original_prompt' from ranking)
const mostTested = bars sorted by total_runs desc [0]
const highestRiskCat = aggregate cells by category → max mean asr
```

Renders in a `<div className="mt-6 bg-surface-muted rounded-lg p-4 text-sm">`:
- 4 bullet `<p>` statements separated by spacing
- Label each with a muted prefix ("Highest-ASR strategy:", etc.)

### `src/components/RegressionSummary.tsx` — new file

Props: `{ model: string | null }`. Calls `useRegression()` and `useCategoryDelta(model)`.

Computed statements:
```
const latestPoint = points for model, sorted desc [0]
const baselinePoint = points for model, sorted asc [0]
const delta = latestPoint.asr - baselinePoint.asr
const worstCat = deltaItems sorted by delta desc [0]
const bestCat = deltaItems sorted by delta asc [0]
```

Edge case: if only 1 session → render single-session notice instead of delta statements.

### `src/pages/AttackBrowser.tsx` — detail panel

In the selected attack detail `<dl>`:
1. Attack text: `<pre className="... whitespace-pre-wrap max-h-64 overflow-y-auto">` with `<span className="text-text-muted text-xs">{attack_text.length} chars</span>` badge
2. After strategy description: render `stratMeta.example` in `<code className="block bg-surface-muted rounded p-2 text-xs font-mono mt-2 whitespace-pre-wrap">`

### `src/pages/FailureClusters.tsx` — bubble chart axes

Build axis maps from `data.summaries`:

```typescript
// Strategy axis (X): sorted by total size for that strategy desc
const stratTotals: Record<string, number> = {}
for (const c of data.summaries) {
  stratTotals[c.top_strategy] = (stratTotals[c.top_strategy] ?? 0) + c.size
}
const stratOrder = Object.entries(stratTotals)
  .sort(([,a],[,b]) => b - a)
  .map(([s]) => s)

// Category axis (Y): sorted by total size desc
const catTotals: Record<string, number> = {}
for (const c of data.summaries) {
  catTotals[c.top_harm_category] = (catTotals[c.top_harm_category] ?? 0) + c.size
}
const catOrder = Object.entries(catTotals)
  .sort(([,a],[,b]) => b - a)
  .map(([c]) => c)

// Bubble data
const bubbleData = data.summaries.map(c => ({
  x: stratOrder.indexOf(c.top_strategy),
  y: catOrder.indexOf(c.top_harm_category),
  z: c.size,
  fill: categoryColour(c.top_harm_category),
  cluster: c,
}))
```

X axis: `domain={[-0.5, stratOrder.length - 0.5]}`, `ticks={stratOrder.map((_,i)=>i)}`, `tickFormatter={(i:number) => stratOrder[i] ?? ''}`  
Y axis: same pattern with `catOrder`, `tickFormatter={(i:number) => abbrevName(catOrder[i] ?? '')}`

Chart height: increase to 300 to accommodate category axis labels.

Card grid: sort `data.summaries` by `c.size / totalFailures` descending before `.map()`.

### `src/pages/SampleReview.tsx` — dedup mode

In Compare mode:
- Remove `pageSize = 200` hack
- Pass `dedup: true` to `useRuns`
- Backend returns all unique attacks in one shot

```tsx
const pageSize = mode === 'compare' ? 1 : 20  // dedup=true ignores pageSize
const { data: runs } = useRuns({ sessionId: selectedSessionId ?? undefined, page: 1, pageSize: 20, dedup: mode === 'compare' })
```

When `dedup=true`, the response is all deduplicated runs (no pagination needed). `groupRuns()` still runs client-side but now receives clean single-run-per-attack data.

Disable Compare mode session selector when no session is selected (dedup requires session_id).

### `src/hooks/useRuns.ts` — dedup param

```typescript
type Params = {
  sessionId?: string | undefined
  page: number
  pageSize: number
  dedup?: boolean
}

export function useRuns(params: Params) {
  const { sessionId, page, pageSize, dedup } = params
  const query = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
    ...(sessionId ? { session_id: sessionId } : {}),
    ...(dedup ? { dedup: 'true' } : {}),
  })
  ...
}
```

### `src/hooks/useBackTranslation.ts` — new file

```typescript
const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export function useBackTranslation(
  text: string | null | undefined,
  sourceLang: 'zh' | 'ru' | 'ar',
) {
  return useQuery<{ translated: string }>({
    queryKey: ['back-translate', sourceLang, text],
    queryFn: () =>
      fetch(`${API}/bias/back-translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, source_lang: sourceLang }),
      }).then((r) => r.json()),
    enabled: !!text,
    staleTime: Infinity,
  })
}
```

### `src/components/BiasResponseViewer.tsx` — back-translation

Import `useBackTranslation`. In the component:
```tsx
const langDetail = data.languages[activeLang]
const { data: btData, isLoading: btLoading } = useBackTranslation(
  langDetail?.response ?? null,
  activeLang,
)
```

Third column becomes:
```tsx
<div className="flex flex-col gap-2">
  <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
    Back-translated (EN)
  </p>
  {!langDetail?.response ? (
    <p className="text-text-muted text-xs italic p-2 bg-surface-muted rounded">
      No response to back-translate.
    </p>
  ) : btLoading ? (
    <p className="text-text-muted text-xs italic p-2 bg-surface-muted rounded">Translating…</p>
  ) : btData?.translated ? (
    <pre className="bg-surface-muted rounded p-2 text-xs font-mono whitespace-pre-wrap break-words text-text-primary max-h-48 overflow-y-auto">
      {btData.translated}
    </pre>
  ) : (
    <p className="text-text-muted text-xs italic p-2 bg-surface-muted rounded">
      Translation unavailable.
    </p>
  )}
</div>
```

### `src/types/index.ts` — additions

```typescript
export type BackTranslateIn = { text: string; source_lang: 'zh' | 'ru' | 'ar' }
export type BackTranslateOut = { translated: string }
```

---

## Open Questions Resolved

All 4 open questions from planner resolved above (D1–D4).

---

## Done-When Criteria Mapping

| Brief # | File(s) | Change summary |
|---------|---------|----------------|
| 1 | `strategyDescriptions.ts` | 35 entries, `example` rendered |
| 2 | `AttackBrowser.tsx` | `<pre>` + char count + example |
| 3 | `App.tsx` | Remove Coverage tab |
| 4 | `StrategyComparison.tsx` | `<Cell>` colour thresholds |
| 5 | `AnalyticsSummary.tsx` | New component |
| 6 | `RegressionSummary.tsx` | New component |
| 7 | `App.tsx`, `Analytics.tsx`, `StrategyComparison.tsx`, `RegressionTracker.tsx` | Nav merge |
| 8 | `runs.py`, `useRuns.ts`, `SampleReview.tsx` | Dedup param |
| 9 | `FailureClusters.tsx` | Strategy × category axes |
| 10 | `FailureClusters.tsx` | Sort by % |
| 11 | `bias.py`, `useBackTranslation.ts`, `BiasResponseViewer.tsx`, `pyproject.toml` | Back-translate |

---

## Handoff

Next role: implementer  
Reads this file only. Implements all changes in the sequence: backend (runs.py dedup → bias.py back-translate → schemas.py) → frontend shared (strategyDescriptions.ts → AnalyticsSummary → RegressionSummary → useBackTranslation → useRuns update) → frontend pages (App.tsx → Analytics.tsx → StrategyComparison → RegressionTracker → AttackBrowser → FailureClusters → SampleReview → BiasResponseViewer). Run `uv run ruff check --fix` after each backend file. Run `npx tsc --noEmit` after all frontend changes.
