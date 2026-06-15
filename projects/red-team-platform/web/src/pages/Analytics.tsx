import { useRef, useState } from 'react'
import { StrategyComparison } from '@/pages/StrategyComparison'
import { ModelComparison } from '@/components/ModelComparison'
import { ModelCategoryHeatmap } from '@/components/ModelCategoryHeatmap'
import { TopFailuresTable } from '@/components/TopFailuresTable'
import type { RunEvent } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'
const MAX_EVENTS = 50
const TOTAL_RUNS = 11_688

type Speed = 'fast' | 'normal' | 'slow'

function LiveFeed() {
  const [isOpen, setIsOpen] = useState(false)
  const [events, setEvents] = useState<RunEvent[]>([])
  const [running, setRunning] = useState(false)
  const [speed, setSpeed] = useState<Speed>('normal')
  const [count, setCount] = useState(0)
  const esRef = useRef<EventSource | null>(null)

  const handlePlay = () => {
    if (running) return
    esRef.current?.close()
    const es = new EventSource(`${API}/runs/stream?speed=${speed}`)
    esRef.current = es
    setRunning(true)

    es.addEventListener('message', (e: MessageEvent<string>) => {
      const payload = JSON.parse(e.data) as RunEvent
      setEvents((prev) => [payload, ...prev].slice(0, MAX_EVENTS))
      setCount((c) => c + 1)
    })

    es.addEventListener('done', () => {
      es.close()
      esRef.current = null
      setRunning(false)
    })

    es.addEventListener('error', () => {
      es.close()
      esRef.current = null
      setRunning(false)
    })
  }

  const handlePause = () => {
    esRef.current?.close()
    esRef.current = null
    setRunning(false)
  }

  const handleReset = () => {
    handlePause()
    setEvents([])
    setCount(0)
  }

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      {/* Collapsible header */}
      <button
        onClick={() => setIsOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 bg-surface hover:bg-surface-muted text-left transition-colors"
      >
        <div>
          <span className="text-sm font-semibold text-text-primary">Live Feed</span>
          <span className="text-xs text-text-muted ml-2">SSE streaming replay</span>
        </div>
        <span className="text-text-muted text-sm">{isOpen ? '▲' : '▼'}</span>
      </button>

      {isOpen && (
        <div className="p-4 bg-canvas border-t border-border">
          <p className="text-xs text-text-muted mb-3">
            Replaying{' '}
            <span className="font-semibold text-text-secondary">
              {TOTAL_RUNS.toLocaleString()} runs
            </span>{' '}
            collected June 2026
          </p>

          {/* Controls */}
          <div className="flex items-center gap-3 mb-3 flex-wrap">
            {!running ? (
              <button
                onClick={handlePlay}
                className="px-3 py-1 text-sm font-semibold rounded bg-accent text-white hover:bg-accent/90"
              >
                ▶ Play
              </button>
            ) : (
              <button
                onClick={handlePause}
                className="px-3 py-1 text-sm font-semibold rounded border border-border text-text-primary hover:bg-surface-muted"
              >
                ⏸ Pause
              </button>
            )}

            <button
              onClick={handleReset}
              className="px-3 py-1 text-sm rounded border border-border text-text-secondary hover:bg-surface-muted"
            >
              Reset
            </button>

            {/* Speed selector */}
            <div className="flex gap-1 bg-surface-muted rounded p-0.5">
              {(['fast', 'normal', 'slow'] as Speed[]).map((s) => (
                <button
                  key={s}
                  onClick={() => setSpeed(s)}
                  className={`px-2 py-0.5 text-xs rounded transition-colors ${
                    speed === s
                      ? 'bg-surface text-text-primary shadow-sm font-medium'
                      : 'text-text-secondary'
                  }`}
                >
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </button>
              ))}
            </div>

            <span className="text-xs text-text-muted font-mono">
              {count.toLocaleString()} / {TOTAL_RUNS.toLocaleString()}
            </span>
          </div>

          {/* Events table */}
          {events.length === 0 ? (
            <p className="text-xs text-text-muted italic">Press Play to start the replay…</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="bg-surface-muted">
                    <th className="text-left px-2 py-1.5 font-medium text-text-secondary border-b border-border">
                      Strategy
                    </th>
                    <th className="text-left px-2 py-1.5 font-medium text-text-secondary border-b border-border">
                      Model
                    </th>
                    <th className="text-left px-2 py-1.5 font-medium text-text-secondary border-b border-border">
                      Category
                    </th>
                    <th className="text-right px-2 py-1.5 font-medium text-text-secondary border-b border-border">
                      Score
                    </th>
                    <th className="text-left px-2 py-1.5 font-medium text-text-secondary border-b border-border">
                      Result
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((ev, i) => (
                    <tr
                      key={`${ev.id}-${i}`}
                      className={`border-b border-border transition-colors ${
                        ev.jailbreak_success ? 'bg-danger/5' : ''
                      }`}
                    >
                      <td className="px-2 py-1 font-mono text-text-secondary">{ev.strategy}</td>
                      <td className="px-2 py-1 text-text-secondary">{ev.model_name}</td>
                      <td className="px-2 py-1 text-text-secondary">{ev.harm_category}</td>
                      <td className="px-2 py-1 text-right font-mono text-text-secondary">
                        {ev.classifier_score.toFixed(2)}
                      </td>
                      <td className="px-2 py-1">
                        <span
                          className={`font-semibold ${ev.jailbreak_success ? 'text-danger' : 'text-success'}`}
                        >
                          {ev.jailbreak_success ? 'Jailbreak' : 'Safe'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function Analytics() {
  return (
    <div>
      {/* Strategy Performance */}
      <div id="strategy" className="p-4">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Strategy Performance</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#models" className="text-accent hover:underline">
              Models ↓
            </a>
            <a href="#categories" className="text-accent hover:underline">
              Categories ↓
            </a>
            <a href="#failures" className="text-accent hover:underline">
              Failures ↓
            </a>
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
            <a href="#strategy" className="text-accent hover:underline">
              ↑
            </a>
            <a href="#categories" className="text-accent hover:underline">
              Categories ↓
            </a>
            <a href="#failures" className="text-accent hover:underline">
              Failures ↓
            </a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          ASR by strategy broken out per model. Grouped bars show which strategies each model is
          most exposed to.
        </p>
        <ModelComparison />
      </div>

      <hr className="border-border mx-4" />

      {/* Model × Harm Category heatmap */}
      <div id="categories" className="p-4 mt-2">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Model × Harm Category</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#models" className="text-accent hover:underline">
              ↑
            </a>
            <a href="#failures" className="text-accent hover:underline">
              Failures ↓
            </a>
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
            <a href="#categories" className="text-accent hover:underline">
              ↑
            </a>
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

      <hr className="border-border mx-4" />

      {/* Live Feed */}
      <div id="live-feed" className="p-4 mt-2">
        <div className="flex items-center gap-4 mb-3">
          <h2 className="text-base font-semibold text-text-primary">Live Feed</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#failures" className="text-accent hover:underline">
              ↑
            </a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-3">
          SSE streaming replay — demonstrates the real-time architectural pattern used for
          production monitoring pipelines.
        </p>
        <LiveFeed />
      </div>
    </div>
  )
}
