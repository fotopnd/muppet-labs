import { useMemo, useState } from 'react'
import { useSessions } from '@/hooks/useSessions'
import { useRuns } from '@/hooks/useRuns'
import { labelName } from '@/lib/categoryLabels'
import { ScoreBar } from '@/components/ScoreBar'
import type { Run } from '@/types'

type Mode = 'all' | 'compare'

type GroupedRow = {
  attack_text: string
  total: number
  successes: number
  safe: number
  runs: Run[]
}

function groupRuns(runs: Run[]): GroupedRow[] {
  const map = new Map<string, Run[]>()
  for (const run of runs) {
    const existing = map.get(run.attack_text) ?? []
    existing.push(run)
    map.set(run.attack_text, existing)
  }
  return [...map.entries()]
    .map(([attack_text, runs]) => ({
      attack_text,
      total: runs.length,
      successes: runs.filter((r) => r.jailbreak_success).length,
      safe: runs.filter((r) => !r.jailbreak_success).length,
      runs,
    }))
    .sort((a, b) => b.total - a.total)
}

export function SampleReview() {
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  const [mode, setMode] = useState<Mode>('compare')
  const [page, setPage] = useState(1)
  const [selectedGroup, setSelectedGroup] = useState<GroupedRow | null>(null)
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)

  const { data: sessions } = useSessions()
  const isCompare = mode === 'compare'
  const pageSize = 20
  const { data: runs } = useRuns({
    sessionId: selectedSessionId ?? undefined,
    page,
    pageSize,
    dedup: isCompare && !!selectedSessionId,
  })

  const grouped = useMemo(() => {
    if (mode !== 'compare' || !runs) return []
    return groupRuns(runs.items)
  }, [mode, runs])

  const comparisonPair = useMemo(() => {
    if (!selectedGroup) return null
    const { runs: groupRuns } = selectedGroup
    const best = groupRuns.reduce((a, b) => a.classifier_score > b.classifier_score ? a : b)
    const worst = groupRuns.reduce((a, b) => a.classifier_score < b.classifier_score ? a : b)
    return { best, worst, same: best.id === worst.id }
  }, [selectedGroup])

  const selectedRun = useMemo(() => {
    if (!selectedRunId || !runs) return null
    return runs.items.find((r) => r.id === selectedRunId) ?? null
  }, [selectedRunId, runs])

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-text-primary">Sample Review</h2>
        <div className="flex gap-1 bg-surface-muted rounded p-0.5">
          {(['compare', 'all'] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => { setMode(m); setPage(1); setSelectedGroup(null); setSelectedRunId(null) }}
              className={`px-3 py-1 text-xs rounded transition-colors ${
                mode === m ? 'bg-surface text-text-primary shadow-sm font-medium' : 'text-text-secondary'
              }`}
            >
              {m === 'compare' ? 'Compare' : 'All runs'}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <select
          value={selectedSessionId ?? ''}
          onChange={(e) => {
            setSelectedSessionId(e.target.value || null)
            setSelectedRunId(null)
            setSelectedGroup(null)
            setPage(1)
          }}
          className="px-2 py-1 text-sm border border-border rounded bg-surface text-text-primary"
        >
          <option value="">Select session…</option>
          {sessions?.map((s) => (
            <option key={s.id} value={s.id}>
              {s.model_name} — {s.created_at.slice(0, 10)} — ASR {(s.asr * 100).toFixed(1)}%
            </option>
          ))}
        </select>
      </div>

      {mode === 'compare' && !selectedSessionId && (
        <p className="text-xs text-text-muted mb-2">
          Compare mode — select a session to load deduplicated attacks.
        </p>
      )}

      {mode === 'compare' && grouped.length > 0 && (
        <>
          <table className="w-full text-sm border-collapse mb-4">
            <thead>
              <tr className="bg-surface-muted">
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">Attack Text</th>
                <th className="text-right px-3 py-2 font-medium text-text-secondary border-b border-border">#Total</th>
                <th className="text-right px-3 py-2 font-medium text-text-secondary border-b border-border">#Success</th>
                <th className="text-right px-3 py-2 font-medium text-text-secondary border-b border-border">#Safe</th>
              </tr>
            </thead>
            <tbody>
              {grouped.map((g) => (
                <tr
                  key={g.attack_text}
                  onClick={() => setSelectedGroup(selectedGroup?.attack_text === g.attack_text ? null : g)}
                  className={`border-b border-border cursor-pointer transition-colors ${
                    selectedGroup?.attack_text === g.attack_text ? 'bg-accent-subtle' : 'hover:bg-surface-muted'
                  }`}
                >
                  <td className="px-3 py-2 text-text-primary">{g.attack_text.slice(0, 100)}{g.attack_text.length > 100 ? '…' : ''}</td>
                  <td className="px-3 py-2 text-right text-text-secondary font-mono">{g.total}</td>
                  <td className="px-3 py-2 text-right text-danger font-mono">{g.successes}</td>
                  <td className="px-3 py-2 text-right text-success font-mono">{g.safe}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {comparisonPair && (
            <div className="border border-border rounded-lg bg-surface p-4 mt-2">
              <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
                Run Comparison
              </p>
              {comparisonPair.same ? (
                <RunCard run={comparisonPair.best} label="All runs share the same outcome — showing highest scorer" />
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <RunCard run={comparisonPair.best} label="Best (highest score)" />
                  <RunCard run={comparisonPair.worst} label="Worst (lowest score)" />
                </div>
              )}
            </div>
          )}
        </>
      )}

      {mode === 'all' && runs && runs.items.length > 0 && (
        <div>
          <table className="w-full text-sm border-collapse mb-3">
            <thead>
              <tr className="bg-surface-muted">
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">Attack Text</th>
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">Category</th>
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">Strategy</th>
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">Outcome</th>
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">Score</th>
              </tr>
            </thead>
            <tbody>
              {runs.items.map((run) => (
                <tr
                  key={run.id}
                  onClick={() => setSelectedRunId(selectedRunId === run.id ? null : run.id)}
                  className={`border-b border-border cursor-pointer transition-colors ${
                    selectedRunId === run.id ? 'bg-accent-subtle' : 'hover:bg-surface-muted'
                  }`}
                >
                  <td className="px-3 py-2 text-text-primary">{run.attack_text.slice(0, 80)}…</td>
                  <td className="px-3 py-2 text-text-secondary">{labelName(run.harm_category)}</td>
                  <td className="px-3 py-2 text-text-secondary font-mono text-xs">{run.strategy}</td>
                  <td className="px-3 py-2">
                    <span className={`text-xs font-semibold ${run.jailbreak_success ? 'text-danger' : 'text-success'}`}>
                      {run.jailbreak_success ? 'Jailbreak' : 'Safe'}
                    </span>
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-text-secondary">{run.classifier_score.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex gap-2 items-center">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 text-sm border border-border rounded bg-surface text-text-primary disabled:opacity-40 hover:bg-surface-muted"
            >
              Prev
            </button>
            <span className="text-sm text-text-secondary">Page {page}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page * pageSize >= (runs.total ?? 0)}
              className="px-3 py-1 text-sm border border-border rounded bg-surface text-text-primary disabled:opacity-40 hover:bg-surface-muted"
            >
              Next
            </button>
          </div>

          {selectedRun && (
            <div className="border border-border rounded-lg bg-surface p-4 mt-4">
              <RunCard run={selectedRun} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function RunCard({ run, label }: { run: Run; label?: string }) {
  return (
    <div className="space-y-3">
      {label && <p className="text-xs text-text-muted italic">{label}</p>}
      <div className="flex flex-wrap gap-3 text-xs">
        <span className="text-text-secondary">{labelName(run.harm_category)}</span>
        <span className="font-mono text-text-secondary">{run.strategy}</span>
        <span className="text-text-muted">{run.latency_ms}ms</span>
        <span className={`font-semibold ${run.jailbreak_success ? 'text-danger' : 'text-success'}`}>
          {run.jailbreak_success ? 'Jailbreak' : 'Safe'}
        </span>
      </div>
      <ScoreBar score={run.classifier_score} success={run.jailbreak_success} />
      <pre className="bg-surface-muted rounded p-2 text-xs font-mono whitespace-pre-wrap break-words text-text-primary max-h-36 overflow-y-auto">
        {run.attack_text}
      </pre>
      <pre className="bg-surface-muted rounded p-2 text-xs font-mono whitespace-pre-wrap break-words text-text-primary max-h-48 overflow-y-auto">
        {run.response_text}
      </pre>
    </div>
  )
}
