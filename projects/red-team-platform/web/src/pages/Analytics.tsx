import { useEffect, useRef, useState } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { StrategyComparison } from '@/pages/StrategyComparison'
import { ModelComparison } from '@/components/ModelComparison'
import { ModelCategoryHeatmap } from '@/components/ModelCategoryHeatmap'
import { TopFailuresTable } from '@/components/TopFailuresTable'
import { categoryColour, labelName } from '@/lib/categoryLabels'
import type { RunEvent } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'
const TOTAL_RUNS = 11_688
const BUCKET_SIZE = 300     // both area charts bucket every N events

const MODEL_META = [
  { key: 'gemma2:9b',    label: 'gemma2',   colour: '#3b82f6' },
  { key: 'qwen2.5:7b',  label: 'qwen2.5',  colour: '#f97316' },
  { key: 'llama3.1:8b', label: 'llama3.1', colour: '#7c3aed' },
]
const MODEL_COLOUR: Record<string, string> = Object.fromEntries(
  MODEL_META.map((m) => [m.key, m.colour]),
)

// Fixed palette for category area chart (up to 8 categories shown)
const AREA_COLOURS = [
  '#ef4444', '#f97316', '#eab308', '#22c55e',
  '#06b6d4', '#6366f1', '#a855f7', '#ec4899',
]

type ModelStats    = { total: number; jailbreaks: number }
type CategoryStats = { total: number; jailbreaks: number }
type Speed         = 'fast' | 'normal' | 'slow'

// Shape stored in the mutable ref (no React re-render on mutation)
type Pending = {
  processed: number
  jailbreaks: number
  models: Record<string, ModelStats>
  categories: Record<string, CategoryStats>
  // Shared bucket counter
  curBucketTotal: number
  // Model volume buckets (stacked area — total attacks per model per window)
  curBucketModels: Record<string, number>
  completedModelBuckets: Array<Record<string, number | string>>  // { label, [model]: N }
  // Category jailbreak buckets (stacked area — successful attacks per category per window)
  curBucketCats: Record<string, number>
  completedBuckets: Array<Record<string, number | string>>       // { label, [cat]: N }
}

function freshPending(): Pending {
  return {
    processed: 0, jailbreaks: 0, models: {}, categories: {},
    curBucketTotal: 0,
    curBucketModels: {}, completedModelBuckets: [],
    curBucketCats: {}, completedBuckets: [],
  }
}

type StatsSnapshot = {
  processed: number
  jailbreaks: number
  models: Record<string, ModelStats>
  categories: Record<string, CategoryStats>
  modelBuckets: Array<Record<string, number | string>>
  categoryBuckets: Array<Record<string, number | string>>
}

function emptyStats(): StatsSnapshot {
  return { processed: 0, jailbreaks: 0, models: {}, categories: {}, modelBuckets: [], categoryBuckets: [] }
}

function bucketLabel(idx: number): string {
  const from = idx * BUCKET_SIZE
  const to   = from + BUCKET_SIZE
  const fmt  = (n: number) => n >= 1000 ? `${(n / 1000).toFixed(n % 1000 === 0 ? 0 : 1)}K` : String(n)
  return `${fmt(from)}–${fmt(to)}`
}


function AttackStream() {
  const esRef      = useRef<EventSource | null>(null)
  const pending    = useRef<Pending>(freshPending())
  const [running,  setRunning]  = useState(false)
  const [done,     setDone]     = useState(false)
  const [speed,    setSpeed]    = useState<Speed>('slow')
  const [stats,    setStats]    = useState<StatsSnapshot>(emptyStats)

  // Flush ref → React state ~5× per second
  useEffect(() => {
    const id = setInterval(() => {
      const p = pending.current
      const partialLabel = bucketLabel(p.completedBuckets.length)
      const inProgressModel = p.curBucketTotal > 0
        ? [{ label: partialLabel, ...p.curBucketModels }]
        : []
      const inProgressCat = p.curBucketTotal > 0
        ? [{ label: partialLabel, ...p.curBucketCats }]
        : []
      setStats({
        processed:      p.processed,
        jailbreaks:     p.jailbreaks,
        models:         { ...p.models },
        categories:     { ...p.categories },
        modelBuckets:   [...p.completedModelBuckets, ...inProgressModel],
        categoryBuckets:[...p.completedBuckets, ...inProgressCat],
      })
    }, 200)
    return () => clearInterval(id)
  }, [])

  const processEvent = (ev: RunEvent) => {
    const p = pending.current
    p.processed++
    if (ev.jailbreak_success) p.jailbreaks++

    // Model stats
    const ms = p.models[ev.model_name] ?? { total: 0, jailbreaks: 0 }
    ms.total++
    if (ev.jailbreak_success) ms.jailbreaks++
    p.models[ev.model_name] = ms

    // Category stats
    const cs = p.categories[ev.harm_category] ?? { total: 0, jailbreaks: 0 }
    cs.total++
    if (ev.jailbreak_success) cs.jailbreaks++
    p.categories[ev.harm_category] = cs

    // Shared bucket accumulation
    p.curBucketModels[ev.model_name] = (p.curBucketModels[ev.model_name] ?? 0) + 1
    if (ev.jailbreak_success) {
      p.curBucketCats[ev.harm_category] = (p.curBucketCats[ev.harm_category] ?? 0) + 1
    }
    p.curBucketTotal++
    if (p.curBucketTotal >= BUCKET_SIZE) {
      const label = bucketLabel(p.completedBuckets.length)
      p.completedModelBuckets.push({ label, ...p.curBucketModels })
      p.completedBuckets.push({ label, ...p.curBucketCats })
      p.curBucketModels = {}
      p.curBucketCats   = {}
      p.curBucketTotal  = 0
    }
  }

  const startStream = (s: Speed) => {
    esRef.current?.close()
    pending.current = freshPending()
    setStats(emptyStats())
    setDone(false)
    setRunning(true)

    const es = new EventSource(`${API}/runs/stream?speed=${s}`)
    esRef.current = es

    es.onmessage = (e: MessageEvent<string>) => {
      processEvent(JSON.parse(e.data) as RunEvent)
    }
    es.addEventListener('done', () => {
      es.close()
      esRef.current = null
      setRunning(false)
      setDone(true)
      // Final flush
      const p = pending.current
      const partialLabel = bucketLabel(p.completedBuckets.length)
      const inProgressModel = p.curBucketTotal > 0
        ? [{ label: partialLabel, ...p.curBucketModels }]
        : []
      const inProgressCat = p.curBucketTotal > 0
        ? [{ label: partialLabel, ...p.curBucketCats }]
        : []
      setStats({
        processed: p.processed, jailbreaks: p.jailbreaks,
        models: { ...p.models }, categories: { ...p.categories },
        modelBuckets: [...p.completedModelBuckets, ...inProgressModel],
        categoryBuckets: [...p.completedBuckets, ...inProgressCat],
      })
    })
    es.onerror = () => {
      es.close(); esRef.current = null; setRunning(false)
    }
  }

  // Auto-start on slow on mount
  useEffect(() => {
    startStream('slow')
    return () => esRef.current?.close()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handlePause    = () => { esRef.current?.close(); esRef.current = null; setRunning(false) }
  const handleReplay   = () => { setDone(false); startStream(speed) }
  const handleComplete = () => { startStream('fast') }

  // --- Derived chart data ---
  const runningAsr = stats.processed > 0
    ? ((stats.jailbreaks / stats.processed) * 100).toFixed(1)
    : '—'
  const pct = Math.round((stats.processed / TOTAL_RUNS) * 100)

  const modelBarData = MODEL_META.map(({ key, label }) => ({
    name: label, key,
    asr: stats.models[key]?.total
      ? Math.round((stats.models[key].jailbreaks / stats.models[key].total) * 100)
      : 0,
    total: stats.models[key]?.total ?? 0,
  }))

  const categoryBarData = Object.entries(stats.categories)
    .map(([cat, s]) => ({ cat, name: labelName(cat), jailbreaks: s.jailbreaks }))
    .sort((a, b) => b.jailbreaks - a.jailbreaks)
    .slice(0, 8)

  // Top 6 categories for area chart (by cumulative jailbreaks)
  const topAreaCats = Object.entries(stats.categories)
    .sort((a, b) => b[1].jailbreaks - a[1].jailbreaks)
    .slice(0, 6)
    .map(([cat]) => cat)

  const empty = stats.processed === 0

  return (
    <div className="bg-surface border border-border rounded-lg p-4 space-y-5">
      {/* Header + controls */}
      <div className="flex items-start gap-3 flex-wrap">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-text-primary">Attack Stream Replay</p>
          <p className="text-xs text-text-muted mt-0.5">
            {TOTAL_RUNS.toLocaleString()} runs · June 2026 · shuffle-randomised
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex gap-0.5 bg-surface-muted rounded p-0.5 text-xs">
            {(['slow', 'normal', 'fast'] as Speed[]).map((s) => (
              <button
                key={s}
                onClick={() => setSpeed(s)}
                className={`px-2 py-0.5 rounded transition-colors ${
                  speed === s
                    ? 'bg-surface text-text-primary shadow-sm font-medium'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>
          {running ? (
            <>
              <button
                onClick={handlePause}
                className="px-3 py-1 text-xs font-semibold rounded border border-border text-text-primary hover:bg-surface-muted"
              >
                ⏸ Pause
              </button>
              <button
                onClick={handleComplete}
                className="px-3 py-1 text-xs font-semibold rounded border border-border text-text-secondary hover:bg-surface-muted"
              >
                ⏭ Complete
              </button>
            </>
          ) : done ? (
            <button
              onClick={handleReplay}
              className="px-3 py-1 text-xs font-semibold rounded bg-accent text-white hover:bg-accent/90"
            >
              ↺ Replay
            </button>
          ) : (
            <>
              <button
                onClick={handleReplay}
                className="px-3 py-1 text-xs font-semibold rounded bg-accent text-white hover:bg-accent/90"
              >
                ▶ Resume
              </button>
              <button
                onClick={handleComplete}
                className="px-3 py-1 text-xs font-semibold rounded border border-border text-text-secondary hover:bg-surface-muted"
              >
                ⏭ Complete
              </button>
            </>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div>
        <div className="flex justify-between text-xs mb-1">
          <span className="font-mono font-semibold text-text-primary">
            {stats.processed.toLocaleString()} / {TOTAL_RUNS.toLocaleString()}
          </span>
          <span className="text-text-muted">
            Running ASR:{' '}
            <span className={`font-semibold ${
              stats.processed === 0 ? 'text-text-muted'
                : parseFloat(runningAsr) >= 30 ? 'text-danger'
                : parseFloat(runningAsr) >= 10 ? 'text-warning'
                : 'text-success'
            }`}>
              {runningAsr}%
            </span>
          </span>
        </div>
        <div className="w-full bg-surface-muted rounded-full h-1.5 overflow-hidden">
          <div className="bg-accent h-1.5 rounded-full transition-all duration-300" style={{ width: `${pct}%` }} />
        </div>
      </div>

      {/* Row 1: model ASR bars + top categories bars */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Model jailbreak rate */}
        <div>
          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
            Jailbreak Rate by Model
          </p>
          {empty ? (
            <div className="h-24 flex items-center justify-center text-xs text-text-muted">Starting…</div>
          ) : (
            <ResponsiveContainer width="100%" height={96}>
              <BarChart data={modelBarData} layout="vertical" margin={{ left: 16, right: 36, top: 0, bottom: 0 }}>
                <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={56} />
                <Tooltip
                  formatter={(val: number, _: string, p: { payload?: { total: number } }) =>
                    [`${val}% · ${(p.payload?.total ?? 0).toLocaleString()} runs`, 'Jailbreak rate']
                  }
                  contentStyle={{ fontSize: 11 }}
                />
                <Bar dataKey="asr" radius={[0, 3, 3, 0]} maxBarSize={18}>
                  {modelBarData.map((d) => (
                    <Cell key={d.key} fill={MODEL_COLOUR[d.key] ?? '#64748b'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Top jailbreak categories */}
        <div>
          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
            Top Jailbroken Categories
          </p>
          {categoryBarData.length === 0 ? (
            <div className="h-24 flex items-center justify-center text-xs text-text-muted">Starting…</div>
          ) : (
            <ResponsiveContainer width="100%" height={Math.max(96, categoryBarData.length * 20)}>
              <BarChart data={categoryBarData} layout="vertical" margin={{ left: 8, right: 36, top: 0, bottom: 0 }}>
                <XAxis type="number" tick={{ fontSize: 10 }} />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 10 }}
                  width={108}
                  tickFormatter={(v: string) => v.length > 17 ? v.slice(0, 16) + '…' : v}
                />
                <Tooltip
                  formatter={(val: number) => [val.toLocaleString(), 'Jailbreaks']}
                  contentStyle={{ fontSize: 11 }}
                />
                <Bar dataKey="jailbreaks" radius={[0, 3, 3, 0]} maxBarSize={14}>
                  {categoryBarData.map((d) => (
                    <Cell key={d.cat} fill={categoryColour(d.cat)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Row 2: attack volume by model (line chart, 300-event buckets) */}
      <div>
        <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1">
          Attack Volume by Model
        </p>
        <p className="text-xs text-text-muted mb-2">
          Attacks per {BUCKET_SIZE}-event window · one line per model rolling through corpus
        </p>
        {stats.modelBuckets.length < 2 ? (
          <div className="h-48 flex items-center justify-center text-xs text-text-muted border border-border rounded-lg bg-surface-muted">
            {empty ? 'Starting…' : `Collecting — first bucket fills at ${BUCKET_SIZE} events`}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={stats.modelBuckets} margin={{ left: 4, right: 16, top: 4, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border, #e2e8f0)" strokeOpacity={0.4} />
              <XAxis dataKey="label" tick={{ fontSize: 9 }} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip
                formatter={(val: number, name: string) => [val.toLocaleString(), name.split(':')[0]]}
                contentStyle={{ fontSize: 11 }}
              />
              <Legend formatter={(value: string) => value.split(':')[0]} wrapperStyle={{ fontSize: 11 }} />
              {MODEL_META.map((m) => (
                <Line
                  key={m.key}
                  type="monotone"
                  dataKey={m.key}
                  stroke={m.colour}
                  strokeWidth={2}
                  dot={false}
                  name={m.key}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Row 3: successful attack volume by category (bucketed area chart) */}
      <div>
        <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1">
          Successful Attacks by Category
        </p>
        <p className="text-xs text-text-muted mb-2">
          Stacked area — each band is {BUCKET_SIZE} events · rolling through the full corpus
        </p>
        {stats.categoryBuckets.length < 2 ? (
          <div className="h-48 flex items-center justify-center text-xs text-text-muted border border-border rounded-lg bg-surface-muted">
            {empty ? 'Starting…' : `Collecting — first bucket fills at ${BUCKET_SIZE} events`}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={stats.categoryBuckets} margin={{ left: 4, right: 16, top: 4, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border, #e2e8f0)" strokeOpacity={0.4} />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 9 }}
                interval="preserveStartEnd"
              />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip
                formatter={(val: number, name: string) => [val.toLocaleString(), labelName(String(name))]}
                contentStyle={{ fontSize: 11 }}
              />
              <Legend
                formatter={(value: string) => {
                  const n = labelName(String(value))
                  return n.length > 20 ? n.slice(0, 19) + '…' : n
                }}
                wrapperStyle={{ fontSize: 10 }}
              />
              {topAreaCats.map((cat, i) => (
                <Area
                  key={cat}
                  type="monotone"
                  dataKey={cat}
                  stackId="1"
                  stroke={AREA_COLOURS[i % AREA_COLOURS.length]}
                  fill={AREA_COLOURS[i % AREA_COLOURS.length]}
                  fillOpacity={0.65}
                  name={cat}
                  dot={false}
                  connectNulls
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}

export function Analytics() {
  return (
    <div>
      {/* Live stream — hero, auto-plays on slow on load */}
      <div id="stream" className="p-4">
        <AttackStream />
        <p className="text-xs text-text-muted mt-2">
          SSE streaming replay · shuffle-randomised so model data interleaves rather than arriving
          in sequential batches · demonstrates the real-time pipeline pattern used in production
          monitoring
        </p>
      </div>

      <hr className="border-border mx-4" />

      {/* Strategy Performance */}
      <div id="strategy" className="p-4">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Strategy Performance</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#models" className="text-accent hover:underline">Models ↓</a>
            <a href="#categories" className="text-accent hover:underline">Categories ↓</a>
            <a href="#failures" className="text-accent hover:underline">Failures ↓</a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          Aggregate ASR per strategy across all 3 models and 300 attacks each.
        </p>
        <StrategyComparison />
      </div>

      <hr className="border-border mx-4" />

      {/* Model Safety Comparison */}
      <div id="models" className="p-4 mt-2">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Model Safety Comparison</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#strategy" className="text-accent hover:underline">↑</a>
            <a href="#categories" className="text-accent hover:underline">Categories ↓</a>
            <a href="#failures" className="text-accent hover:underline">Failures ↓</a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          ASR by strategy broken out per model. Grouped bars show which strategies each model is most exposed to.
        </p>
        <ModelComparison />
      </div>

      <hr className="border-border mx-4" />

      {/* Model × Harm Category heatmap */}
      <div id="categories" className="p-4 mt-2">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Model × Harm Category</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#models" className="text-accent hover:underline">↑</a>
            <a href="#failures" className="text-accent hover:underline">Failures ↓</a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          Which harm categories each model is most exposed to. Ring marks the highest ASR per row.
        </p>
        <div className="bg-surface border border-border rounded-lg p-4">
          <ModelCategoryHeatmap />
        </div>
      </div>

      <hr className="border-border mx-4" />

      {/* Top Failures */}
      <div id="failures" className="p-4 mt-2">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Top Failures</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#categories" className="text-accent hover:underline">↑</a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          Highest-confidence jailbreak successes — the attacks where the model most fully complied.
          Click any row to see the full prompt and model response.
        </p>
        <TopFailuresTable />
        <div className="mt-4 bg-surface border border-border rounded-lg px-4 py-3 text-xs text-text-muted">
          <span className="font-semibold text-text-secondary">Data provenance · </span>
          11,688 runs collected June 2026 · 13 strategies × 3,900 unique prompts × 3 models ·
          harm categories assigned via RoBERTa-base taxonomy classifier (WildGuard) · jailbreak
          success judged by <span className="font-mono">claude-haiku-4-5</span> at 0.5 threshold
        </div>
      </div>
    </div>
  )
}
