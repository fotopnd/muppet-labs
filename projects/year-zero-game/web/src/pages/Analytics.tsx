import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAnalyticsSummary, API_BASE } from '../api/hooks'
import type { AnalyticsSummary } from '../types'

function pct(n: number) {
  return `${(n * 100).toFixed(1)}%`
}

function StatBlock({ label, value, sub }: { label: string; value: string | null; sub?: string }) {
  return (
    <div
      className="flex flex-col gap-1 border p-3"
      style={{
        borderColor: 'var(--color-pixel-gork)',
        background: 'var(--color-pixel-gork-bg)',
      }}
    >
      <span
        className="font-pixel text-[6px] tracking-widest opacity-60"
        style={{ color: 'var(--color-pixel-gork)' }}
      >
        {label}
      </span>
      <span
        className="font-pixel text-[14px]"
        style={{ color: value ? 'var(--color-pixel-gork)' : 'var(--color-pixel-gork)' }}
      >
        {value ?? '—'}
      </span>
      {sub && (
        <span
          className="font-pixel text-[6px] opacity-50"
          style={{ color: 'var(--color-pixel-gork)' }}
        >
          {sub}
        </span>
      )}
    </div>
  )
}

function MiniBar({ label, value, color }: { label: string; value: number; color: string }) {
  const w = Math.round(value * 100)
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between items-baseline">
        <span className="font-pixel text-[6px] opacity-60" style={{ color: 'var(--color-pixel-card-text)' }}>
          {label.replace(/_/g, ' ')}
        </span>
        <span className="font-pixel text-[7px]" style={{ color }}>
          {pct(value)}
        </span>
      </div>
      <div className="h-[4px] w-full" style={{ background: 'var(--color-pixel-desk)' }}>
        <div className="h-full" style={{ width: `${w}%`, background: color }} />
      </div>
    </div>
  )
}

function SparkBars({ data }: { data: Array<{ date: string; count: number }> }) {
  if (data.length === 0) return (
    <span className="font-pixel text-[6px] opacity-40" style={{ color: 'var(--color-pixel-gork)' }}>
      NO DATA YET
    </span>
  )
  const max = Math.max(...data.map(d => d.count), 1)
  return (
    <div className="flex items-end gap-[3px] h-[40px]">
      {data.map((d) => {
        const h = Math.max(2, Math.round((d.count / max) * 40))
        return (
          <div key={d.date} className="flex flex-col items-center gap-1 flex-1">
            <div
              className="w-full"
              style={{ height: `${h}px`, background: 'var(--color-pixel-gork)' }}
              title={`${d.date}: ${d.count}`}
            />
          </div>
        )
      })}
    </div>
  )
}

export default function Analytics() {
  const { data: initial } = useAnalyticsSummary()
  const [data, setData] = useState<AnalyticsSummary | null>(null)

  useEffect(() => {
    if (initial && !data) setData(initial)
  }, [initial, data])

  useEffect(() => {
    const es = new EventSource(`${API_BASE}/analytics/stream`)
    es.onmessage = (e) => {
      try { setData(JSON.parse(e.data as string) as AnalyticsSummary) } catch { /* ignore */ }
    }
    return () => es.close()
  }, [])

  const cats = data ? Object.entries(data.accuracy_by_category).sort(([, a], [, b]) => a - b) : []

  return (
    <div
      className="min-h-svh flex flex-col"
      style={{ background: 'var(--color-pixel-room)' }}
    >
      {/* Header */}
      <div
        className="border-b px-4 py-3 flex items-center justify-between"
        style={{ borderColor: 'var(--color-pixel-gork)', background: 'var(--color-pixel-gork-bg)' }}
      >
        <div>
          <p className="font-pixel text-[8px]" style={{ color: 'var(--color-pixel-gork)' }}>
            GORK-3 // LIVE TELEMETRY
          </p>
          <p className="font-pixel text-[6px] opacity-50 mt-1" style={{ color: 'var(--color-pixel-gork)' }}>
            HUMAN OPERATOR PERFORMANCE MONITORING
          </p>
        </div>
        <Link to="/" className="font-pixel text-[6px] opacity-60 hover:opacity-100" style={{ color: 'var(--color-pixel-gork)' }}>
          [ BACK ]
        </Link>
      </div>

      <div className="flex-1 px-4 py-4 flex flex-col gap-4 max-w-[480px] mx-auto w-full">

        {/* Primary stats */}
        <div className="grid grid-cols-2 gap-2">
          <StatBlock
            label="SESSIONS COMPLETE"
            value={data ? String(data.total_sessions) : null}
            sub={data ? `${data.sessions_today} TODAY` : ''}
          />
          <StatBlock
            label="AVG PLAYER ACCURACY"
            value={data ? pct(data.avg_accuracy) : null}
            sub="NON-ESCALATED DECISIONS"
          />
          <StatBlock
            label="GORK AGREEMENT RATE"
            value={data ? pct(data.agreement_rate) : null}
            sub="PLAYER FOLLOWED GORK-3"
          />
          <StatBlock
            label="OVERRIDE ACCURACY"
            value={data ? pct(data.override_accuracy) : null}
            sub="CORRECT WHEN OVERRIDING"
          />
        </div>

        {/* Secondary stats */}
        <div className="grid grid-cols-2 gap-2">
          <StatBlock
            label="ESCALATION RATE"
            value={data ? pct(data.escalation_rate) : null}
          />
          <StatBlock
            label="AVG DECISION TIME"
            value={data ? `${(data.avg_latency_ms / 1000).toFixed(1)}s` : null}
          />
        </div>

        {/* Sessions over time */}
        <div
          className="border p-3"
          style={{ borderColor: 'var(--color-pixel-gork)', background: 'var(--color-pixel-gork-bg)' }}
        >
          <p className="font-pixel text-[6px] tracking-widest opacity-60 mb-3" style={{ color: 'var(--color-pixel-gork)' }}>
            SESSIONS / DAY (LAST 14)
          </p>
          <SparkBars data={data?.sessions_by_day ?? []} />
        </div>

        {/* Per-category accuracy */}
        {cats.length > 0 && (
          <div
            className="border p-3"
            style={{ borderColor: 'var(--color-pixel-gork)', background: 'var(--color-pixel-gork-bg)' }}
          >
            <p
              className="font-pixel text-[6px] tracking-widest opacity-60 mb-3"
              style={{ color: 'var(--color-pixel-gork)' }}
            >
              PLAYER ACCURACY BY CATEGORY
            </p>
            <div className="flex flex-col gap-3">
              {cats.map(([cat, acc]) => (
                <MiniBar
                  key={cat}
                  label={cat}
                  value={acc}
                  color={
                    acc < 0.5
                      ? 'var(--color-pixel-stamp-redact)'
                      : acc < 0.65
                        ? 'var(--color-pixel-stamp-escalate)'
                        : 'var(--color-pixel-stamp-clear)'
                  }
                />
              ))}
            </div>
          </div>
        )}

        {data?.total_sessions === 0 && (
          <p className="font-pixel text-[6px] text-center opacity-40 mt-4" style={{ color: 'var(--color-pixel-gork)' }}>
            AWAITING OPERATOR DATA. SESSIONS IN PROGRESS WILL APPEAR UPON COMPLETION.
          </p>
        )}
      </div>
    </div>
  )
}
