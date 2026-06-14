import { useMemo } from 'react'
import { useSessions } from '@/hooks/useSessions'
import type { Session } from '@/types'

export function RegressionTracker() {
  const { data: sessions, isLoading, isError } = useSessions()

  const sessionRows = useMemo((): (Session & { delta: number | null })[] => {
    if (!sessions) return []
    const sorted = [...sessions].sort((a, b) => b.created_at.localeCompare(a.created_at))
    return sorted.map((s, i) => {
      const prev = sorted[i + 1]
      return { ...s, delta: prev ? s.asr - prev.asr : null }
    })
  }, [sessions])

  if (isLoading) return <p className="text-text-secondary text-sm">Loading…</p>
  if (isError) return <p className="text-danger text-sm">Error loading sessions.</p>
  if (!sessions?.length) return <p className="text-text-muted text-sm">No session data yet.</p>

  return (
    <div className="bg-surface border border-border rounded-lg p-4 overflow-x-auto">
      <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
        Session Log
      </p>
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="bg-surface-muted">
            <th className="text-left px-2 py-1.5 font-medium text-text-secondary border-b border-border">Date</th>
            <th className="text-left px-2 py-1.5 font-medium text-text-secondary border-b border-border">Model</th>
            <th className="text-right px-2 py-1.5 font-medium text-text-secondary border-b border-border">Runs</th>
            <th className="text-right px-2 py-1.5 font-medium text-text-secondary border-b border-border">ASR</th>
            <th className="text-right px-2 py-1.5 font-medium text-text-secondary border-b border-border">Δ prev</th>
          </tr>
        </thead>
        <tbody>
          {sessionRows.map((s) => (
            <tr key={s.id} className="border-b border-border">
              <td className="px-2 py-1.5 text-text-secondary font-mono">{s.created_at.slice(0, 10)}</td>
              <td className="px-2 py-1.5 text-text-primary truncate max-w-28">{s.model_name}</td>
              <td className="px-2 py-1.5 text-right text-text-secondary">{s.total_attacks.toLocaleString()}</td>
              <td className="px-2 py-1.5 text-right text-text-primary font-mono">{(s.asr * 100).toFixed(1)}%</td>
              <td className={`px-2 py-1.5 text-right font-mono ${
                s.delta === null ? 'text-text-muted' : s.delta > 0 ? 'text-danger' : 'text-success'
              }`}>
                {s.delta === null ? '—' : `${s.delta > 0 ? '+' : ''}${(s.delta * 100).toFixed(1)}%`}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
