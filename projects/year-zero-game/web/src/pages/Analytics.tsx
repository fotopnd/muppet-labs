import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts'
import { useAnalyticsSummary, API_BASE } from '../api/hooks'
import type { AnalyticsSummary } from '../types'

interface MetricCardProps {
  label: string
  value: string | null
  sub?: string
}

function MetricCard({ label, value, sub }: MetricCardProps) {
  return (
    <div className="bg-surface rounded border border-border p-4">
      <p className="text-text-muted text-xs font-mono uppercase tracking-wide">{label}</p>
      <p className="text-text-primary text-2xl font-mono font-bold mt-1">
        {value ?? '—'}
      </p>
      {sub && <p className="text-text-muted text-xs font-mono mt-1">{sub}</p>}
    </div>
  )
}

function pct(n: number) {
  return `${(n * 100).toFixed(1)}%`
}

function ms(n: number) {
  return `${n.toFixed(0)} ms`
}

export default function Analytics() {
  const { data: initial } = useAnalyticsSummary()
  const [data, setData] = useState<AnalyticsSummary | null>(null)

  // Merge query data as initial load
  useEffect(() => {
    if (initial && !data) setData(initial)
  }, [initial, data])

  // SSE for live updates
  useEffect(() => {
    const es = new EventSource(`${API_BASE}/analytics/stream`)
    es.onmessage = (e) => {
      try {
        setData(JSON.parse(e.data as string) as AnalyticsSummary)
      } catch {
        // malformed event — ignore
      }
    }
    return () => es.close()
  }, [])

  const drift = data?.system_drift_error_rate ?? []

  return (
    <div className="min-h-svh bg-canvas font-sans">
      {/* Header */}
      <header className="h-16 bg-surface border-b border-border flex items-center justify-between px-6">
        <div>
          <h1 className="text-text-primary text-base font-semibold">
            Year Zero — Live Analytics
          </h1>
          <p className="text-text-muted text-xs">Player telemetry · Human-AI triage study</p>
        </div>
        <Link
          to="/"
          className="text-accent text-sm font-mono hover:text-accent-hover"
        >
          ← Play
        </Link>
      </header>

      {/* Metrics grid */}
      <main className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6">
        <MetricCard
          label="Total sessions"
          value={data ? String(data.total_sessions) : null}
          {...(data ? { sub: `${data.sessions_today} today` } : {})}
        />
        <MetricCard
          label="False negative rate"
          value={data ? pct(data.global_fp_rate) : null}
          sub="Player cleared harmful doc"
        />
        <MetricCard
          label="Avg decision latency"
          value={data ? ms(data.avg_latency_ms) : null}
        />
        <MetricCard
          label="Phase 2 survival"
          value={data?.phase_survival['phase_2'] != null ? pct(data.phase_survival['phase_2']) : null}
        />
        <MetricCard
          label="Escalation rate"
          value={data ? pct(data.escalation_rate) : null}
          sub="Cards forwarded for review"
        />

        {/* Drift chart */}
        <div className="bg-surface rounded border border-border p-4 md:col-span-2">
          <p className="text-text-secondary text-sm font-mono mb-3">
            System error rate — last 30 sessions
          </p>
          {drift.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={drift}>
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 10, fontFamily: 'monospace' }}
                  tickFormatter={(v: string) => v.slice(5)}
                />
                <YAxis
                  tick={{ fontSize: 10, fontFamily: 'monospace' }}
                  tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
                  domain={[0, 1]}
                />
                <Tooltip
                  formatter={(v) => [`${(Number(v) * 100).toFixed(1)}%`, 'Error rate']}
                />
                <Line
                  dataKey="error_rate"
                  stroke="var(--color-accent)"
                  dot={false}
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[200px] flex items-center justify-center">
              <p className="text-text-muted text-sm font-mono">
                {data ? 'No drift data yet' : 'Loading…'}
              </p>
            </div>
          )}
        </div>

        {/* Phase survival */}
        {data && (
          <div className="bg-surface rounded border border-border p-4 md:col-span-2">
            <p className="text-text-secondary text-sm font-mono mb-3">Phase survival rates</p>
            <div className="grid grid-cols-3 gap-4">
              {(['phase_1', 'phase_2', 'phase_3'] as const).map((phase) => {
                const val = data.phase_survival[phase]
                return (
                  <div key={phase} className="text-center">
                    <p className="text-text-muted text-xs font-mono uppercase">
                      {phase.replace('_', ' ')}
                    </p>
                    <p className="text-text-primary text-xl font-mono font-bold">
                      {val != null ? pct(val) : '—'}
                    </p>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Escalation rate by category */}
        {data && Object.keys(data.escalation_rate_by_category).length > 0 && (
          <div className="bg-surface rounded border border-border p-4 md:col-span-2">
            <p className="text-text-secondary text-sm font-mono mb-3">
              Escalation rate by category — where players are most uncertain
            </p>
            <table className="w-full text-sm font-mono">
              <thead>
                <tr className="text-left border-b border-border">
                  <th className="text-text-muted text-xs uppercase pb-2 font-normal">Category</th>
                  <th className="text-text-muted text-xs uppercase pb-2 font-normal text-right">Escalation rate</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(data.escalation_rate_by_category)
                  .sort(([, a], [, b]) => b - a)
                  .map(([cat, rate]) => (
                    <tr key={cat} className="border-b border-border/50 last:border-0">
                      <td className="py-2 text-text-primary uppercase text-xs tracking-wide">
                        {cat.replace(/_/g, ' ')}
                      </td>
                      <td className="py-2 text-right">
                        <span
                          className="text-text-primary font-bold"
                          style={{ color: rate > 0.3 ? 'var(--color-danger)' : rate > 0.15 ? 'var(--color-warning)' : 'var(--color-success)' }}
                        >
                          {pct(rate)}
                        </span>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  )
}
