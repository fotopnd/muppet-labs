import { useEffect, useRef, useState } from 'react'
import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { StrategyComparison } from '@/pages/StrategyComparison'
import { ModelComparison } from '@/components/ModelComparison'
import { ModelCategoryHeatmap } from '@/components/ModelCategoryHeatmap'
import { TopFailuresTable } from '@/components/TopFailuresTable'
import { labelName } from '@/lib/categoryLabels'
import type { RunEvent } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'
const TOTAL_RUNS = 11_688

// Model identity colours (matches rest of app)
const MODEL_META: { key: string; label: string; colour: string }[] = [
  { key: 'gemma2:9b',    label: 'gemma2',   colour: '#3b82f6' },
  { key: 'qwen2.5:7b',  label: 'qwen2.5',  colour: '#f97316' },
  { key: 'llama3.1:8b', label: 'llama3.1', colour: '#7c3aed' },
]
const MODEL_COLOUR: Record<string, string> = Object.fromEntries(
  MODEL_META.map((m) => [m.key, m.colour]),
)

type ModelStats = { total: number; jailbreaks: number }
type CategoryStats = { total: number; jailbreaks: number }
type Speed = 'fast' | 'normal' | 'slow'

const SPEEDS: Record<Speed, string> = { fast: '0ms', normal: '50ms', slow: '200ms' }

function AttackStream() {
  const esRef = useRef<EventSource | null>(null)
  const [running, setRunning] = useState(false)
  const [done, setDone] = useState(false)
  const [speed, setSpeed] = useState<Speed>('fast')

  // Mutable ref accumulates raw counts — no re-render on every event
  const pending = useRef({
    processed: 0,
    jailbreaks: 0,
    models: {} as Record<string, ModelStats>,
    categories: {} as Record<string, CategoryStats>,
  })

  // React state flushed from ref on interval (~5fps)
  const [stats, setStats] = useState({
    processed: 0,
    jailbreaks: 0,
    models: {} as Record<string, ModelStats>,
    categories: {} as Record<string, CategoryStats>,
  })

  // Flush pending → React state every 200ms
  useEffect(() => {
    const id = setInterval(() => {
      const p = pending.current
      setStats({
        processed: p.processed,
        jailbreaks: p.jailbreaks,
        models: { ...p.models },
        categories: { ...p.categories },
      })
    }, 200)
    return () => clearInterval(id)
  }, [])

  const startStream = (s: Speed = speed) => {
    esRef.current?.close()
    pending.current = { processed: 0, jailbreaks: 0, models: {}, categories: {} }
    setStats({ processed: 0, jailbreaks: 0, models: {}, categories: {} })
    setDone(false)
    setRunning(true)

    const es = new EventSource(`${API}/runs/stream?speed=${s}`)
    esRef.current = es

    es.onmessage = (e: MessageEvent<string>) => {
      const ev = JSON.parse(e.data) as RunEvent
      const p = pending.current
      p.processed++
      if (ev.jailbreak_success) p.jailbreaks++

      const m = p.models[ev.model_name] ?? { total: 0, jailbreaks: 0 }
      m.total++
      if (ev.jailbreak_success) m.jailbreaks++
      p.models[ev.model_name] = m

      const c = p.categories[ev.harm_category] ?? { total: 0, jailbreaks: 0 }
      c.total++
      if (ev.jailbreak_success) c.jailbreaks++
      p.categories[ev.harm_category] = c
    }

    es.addEventListener('done', () => {
      es.close()
      esRef.current = null
      setRunning(false)
      setDone(true)
      // Final flush
      const p = pending.current
      setStats({ processed: p.processed, jailbreaks: p.jailbreaks, models: { ...p.models }, categories: { ...p.categories } })
    })

    es.onerror = () => {
      es.close()
      esRef.current = null
      setRunning(false)
    }
  }

  // Auto-start on mount
  useEffect(() => {
    startStream('fast')
    return () => esRef.current?.close()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handlePause = () => {
    esRef.current?.close()
    esRef.current = null
    setRunning(false)
  }

  const handleReplay = () => {
    setDone(false)
    startStream(speed)
  }

  // Derived chart data
  const runningAsr = stats.processed > 0
    ? ((stats.jailbreaks / stats.processed) * 100).toFixed(1)
    : '—'

  const modelChartData = MODEL_META.map(({ key, label }) => ({
    name: label,
    key,
    asr: stats.models[key]?.total
      ? Math.round((stats.models[key].jailbreaks / stats.models[key].total) * 100)
      : 0,
    total: stats.models[key]?.total ?? 0,
  }))

  const categoryChartData = Object.entries(stats.categories)
    .map(([cat, s]) => ({ name: labelName(cat), jailbreaks: s.jailbreaks }))
    .sort((a, b) => b.jailbreaks - a.jailbreaks)
    .slice(0, 8)

  const pct = stats.processed > 0 ? Math.round((stats.processed / TOTAL_RUNS) * 100) : 0

  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      {/* Header row */}
      <div className="flex items-center gap-3 mb-3 flex-wrap">
        <div>
          <p className="text-sm font-semibold text-text-primary">Attack Stream Replay</p>
          <p className="text-xs text-text-muted mt-0.5">
            {TOTAL_RUNS.toLocaleString()} runs · June 2026 · shuffle-randomised
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2 flex-wrap">
          {/* Speed selector */}
          <div className="flex gap-0.5 bg-surface-muted rounded p-0.5 text-xs">
            {(Object.keys(SPEEDS) as Speed[]).map((s) => (
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
            <button
              onClick={handlePause}
              className="px-3 py-1 text-xs font-semibold rounded border border-border text-text-primary hover:bg-surface-muted"
            >
              ⏸ Pause
            </button>
          ) : (
            <button
              onClick={handleReplay}
              className="px-3 py-1 text-xs font-semibold rounded bg-accent text-white hover:bg-accent/90"
            >
              {done ? '↺ Replay' : '▶ Play'}
            </button>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-text-muted mb-1">
          <span className="font-mono font-semibold text-text-primary">
            {stats.processed.toLocaleString()} / {TOTAL_RUNS.toLocaleString()}
          </span>
          <span>
            Running ASR:{' '}
            <span className={`font-semibold ${
              stats.processed > 0
                ? parseFloat(runningAsr) >= 30 ? 'text-danger' : parseFloat(runningAsr) >= 10 ? 'text-warning' : 'text-success'
                : 'text-text-muted'
            }`}>
              {runningAsr}%
            </span>
          </span>
        </div>
        <div className="w-full bg-surface-muted rounded-full h-1.5 overflow-hidden">
          <div
            className="bg-accent h-1.5 rounded-full transition-all duration-200"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Model ASR */}
        <div>
          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
            Jailbreak Rate by Model
          </p>
          {modelChartData.every((d) => d.total === 0) ? (
            <div className="h-28 flex items-center justify-center text-xs text-text-muted">
              {running ? 'Filling…' : 'Press Play'}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={100}>
              <BarChart data={modelChartData} layout="vertical" margin={{ left: 16, right: 32, top: 0, bottom: 0 }}>
                <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={56} />
                <Tooltip
                  formatter={(val: number, _name: string, props: { payload?: { total: number; jailbreaks?: number } }) => [
                    `${val}% (${props.payload?.total?.toLocaleString() ?? 0} runs)`,
                    'ASR',
                  ]}
                  contentStyle={{ fontSize: 11 }}
                />
                <Bar dataKey="asr" radius={[0, 3, 3, 0]} maxBarSize={20}>
                  {modelChartData.map((d) => (
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
          {categoryChartData.length === 0 ? (
            <div className="h-28 flex items-center justify-center text-xs text-text-muted">
              {running ? 'Filling…' : 'Press Play'}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={Math.max(100, categoryChartData.length * 22)}>
              <BarChart data={categoryChartData} layout="vertical" margin={{ left: 8, right: 32, top: 0, bottom: 0 }}>
                <XAxis type="number" tick={{ fontSize: 10 }} />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 10 }}
                  width={110}
                  tickFormatter={(v: string) => v.length > 16 ? v.slice(0, 15) + '…' : v}
                />
                <Tooltip
                  formatter={(val: number) => [val.toLocaleString(), 'Jailbreaks']}
                  contentStyle={{ fontSize: 11 }}
                />
                <Bar dataKey="jailbreaks" fill="#ef4444" radius={[0, 3, 3, 0]} maxBarSize={16} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}

export function Analytics() {
  return (
    <div>
      {/* Live stream — hero section, visible immediately */}
      <div id="stream" className="p-4">
        <AttackStream />
        <p className="text-xs text-text-muted mt-2">
          SSE streaming replay demonstrates the real-time pipeline pattern used in production
          monitoring. Stream is shuffle-randomised so model data interleaves rather than arriving in
          sequential batches.
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

        {/* Data provenance */}
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
