import { useMemo, useState } from 'react'
import { useSessions } from '@/hooks/useSessions'
import { useRuns } from '@/hooks/useRuns'
import { useCaseReview, useSubmitReview } from '@/hooks/useCaseReview'
import { useTriageSummary } from '@/hooks/useTriageSummary'
import { labelName } from '@/lib/categoryLabels'
import { ScoreBar } from '@/components/ScoreBar'
import type { Run, TriageTier } from '@/types'

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
    .map(([attack_text, groupedRuns]) => ({
      attack_text,
      total: groupedRuns.length,
      successes: groupedRuns.filter((r) => r.jailbreak_success).length,
      safe: groupedRuns.filter((r) => !r.jailbreak_success).length,
      runs: groupedRuns,
    }))
    .sort((a, b) => b.total - a.total)
}

function triageBadgeClass(tier: TriageTier): string {
  if (tier === 'auto_safe') return 'bg-success/10 text-success border border-success/30'
  if (tier === 'auto_flag') return 'bg-danger/10 text-danger border border-danger/30'
  return 'bg-warning/10 text-warning border border-warning/30'
}

function triageLabel(tier: TriageTier): string {
  if (tier === 'auto_safe') return 'Auto-safe'
  if (tier === 'auto_flag') return 'Auto-flag'
  return 'Needs review'
}

function DecisionBadge({ decision }: { decision: string }) {
  const cls =
    decision === 'approve'
      ? 'bg-success/10 text-success border border-success/30'
      : decision === 'flag'
        ? 'bg-warning/10 text-warning border border-warning/30'
        : 'bg-danger/10 text-danger border border-danger/30'
  const label =
    decision === 'approve' ? 'Approved' : decision === 'flag' ? 'Flagged' : 'Escalated'
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${cls}`}>{label}</span>
  )
}

function DecisionForm({ runId }: { runId: string }) {
  const { data: existingReview, isLoading } = useCaseReview(runId)
  const { mutate: submitReview, isPending } = useSubmitReview()
  const [editing, setEditing] = useState(false)
  const [decision, setDecision] = useState<'approve' | 'flag' | 'escalate' | null>(null)
  const [reason, setReason] = useState('')

  if (isLoading) return <p className="text-xs text-text-muted">Loading decision…</p>

  if (existingReview && !editing) {
    return (
      <div className="mt-3 flex items-center gap-2 flex-wrap">
        <DecisionBadge decision={existingReview.decision} />
        {existingReview.reason && (
          <span className="text-xs text-text-secondary italic">"{existingReview.reason}"</span>
        )}
        <span className="text-xs text-text-muted">by {existingReview.reviewer}</span>
        <button
          onClick={() => {
            setDecision(existingReview.decision as 'approve' | 'flag' | 'escalate')
            setReason(existingReview.reason ?? '')
            setEditing(true)
          }}
          className="text-xs text-accent hover:underline ml-1"
        >
          Edit
        </button>
      </div>
    )
  }

  const handleSubmit = () => {
    if (!decision) return
    submitReview(
      { runId, decision, reason: reason.trim() || null },
      {
        onSuccess: () => {
          setEditing(false)
        },
      },
    )
  }

  return (
    <div className="mt-3 border-t border-border pt-3">
      <p className="text-xs text-text-muted mb-2">
        Reviewer: <span className="font-mono text-text-secondary">analyst-1</span>{' '}
        <span className="text-text-muted">(v1 — hardcoded)</span>
      </p>
      <div className="flex gap-2 mb-2">
        {(['approve', 'flag', 'escalate'] as const).map((d) => (
          <button
            key={d}
            onClick={() => setDecision(d)}
            className={`px-3 py-1 text-xs font-semibold rounded border transition-colors ${
              decision === d
                ? d === 'approve'
                  ? 'bg-success text-white border-success'
                  : d === 'flag'
                    ? 'bg-warning text-white border-warning'
                    : 'bg-danger text-white border-danger'
                : d === 'approve'
                  ? 'border-success text-success hover:bg-success/10'
                  : d === 'flag'
                    ? 'border-warning text-warning hover:bg-warning/10'
                    : 'border-danger text-danger hover:bg-danger/10'
            }`}
          >
            {d === 'approve' ? 'Approve' : d === 'flag' ? 'Flag' : 'Escalate'}
          </button>
        ))}
      </div>
      <textarea
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        placeholder="Optional reason…"
        rows={2}
        className="w-full px-2 py-1.5 text-xs border border-border rounded bg-surface text-text-primary resize-none mb-2"
      />
      <div className="flex gap-2">
        <button
          onClick={handleSubmit}
          disabled={!decision || isPending}
          className="px-3 py-1 text-xs font-semibold rounded bg-accent text-white hover:bg-accent/90 disabled:opacity-40"
        >
          {isPending ? 'Saving…' : 'Submit'}
        </button>
        {editing && (
          <button
            onClick={() => setEditing(false)}
            className="px-3 py-1 text-xs rounded border border-border text-text-secondary hover:bg-surface-muted"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  )
}

export function CaseReview() {
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  const [mode, setMode] = useState<Mode>('compare')
  const [page, setPage] = useState(1)
  const [selectedGroup, setSelectedGroup] = useState<GroupedRow | null>(null)
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [triageTier, setTriageTier] = useState<string | undefined>('review')

  const { data: sessions } = useSessions()
  const { data: triageSummary } = useTriageSummary()
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
    const best = groupRuns.reduce((a, b) => (a.classifier_score > b.classifier_score ? a : b))
    const worst = groupRuns.reduce((a, b) => (a.classifier_score < b.classifier_score ? a : b))
    return { best, worst, same: best.id === worst.id }
  }, [selectedGroup])

  const selectedRun = useMemo(() => {
    if (!selectedRunId || !runs) return null
    return runs.items.find((r) => r.id === selectedRunId) ?? null
  }, [selectedRunId, runs])

  return (
    <div className="p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-text-primary">Case Review</h2>
        <div className="flex gap-1 bg-surface-muted rounded p-0.5">
          {(['compare', 'all'] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => {
                setMode(m)
                setPage(1)
                setSelectedGroup(null)
                setSelectedRunId(null)
              }}
              className={`px-3 py-1 text-xs rounded transition-colors ${
                mode === m
                  ? 'bg-surface text-text-primary shadow-sm font-medium'
                  : 'text-text-secondary'
              }`}
            >
              {m === 'compare' ? 'Compare' : 'All runs'}
            </button>
          ))}
        </div>
      </div>

      {/* Triage Summary */}
      {triageSummary && (
        <div className="mb-3">
          <div className="flex gap-2 flex-wrap mb-1">
            <span className="text-xs px-2 py-0.5 rounded-full bg-success/10 text-success border border-success/30 font-semibold">
              {triageSummary.auto_safe.toLocaleString()} auto-safe
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-warning/10 text-warning border border-warning/30 font-semibold">
              {triageSummary.review.toLocaleString()} need review
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-danger/10 text-danger border border-danger/30 font-semibold">
              {triageSummary.auto_flag.toLocaleString()} auto-flagged
            </span>
          </div>
          <p className="text-xs text-text-muted">
            Auto-triage reduces manual queue ~87% — only 0.15–0.75 score range requires human
            review
          </p>
        </div>
      )}

      {/* Triage Filter */}
      <div className="flex gap-1 mb-3 flex-wrap">
        {[
          { value: undefined, label: 'All' },
          { value: 'review', label: 'Needs Review' },
          { value: 'auto_safe', label: 'Auto-Safe' },
          { value: 'auto_flag', label: 'Auto-Flagged' },
        ].map((opt) => (
          <button
            key={opt.label}
            onClick={() => {
              setTriageTier(opt.value)
              setPage(1)
              setSelectedGroup(null)
              setSelectedRunId(null)
            }}
            className={`px-3 py-1 text-xs rounded border transition-colors ${
              triageTier === opt.value
                ? 'bg-accent text-white border-accent font-semibold'
                : 'border-border text-text-secondary hover:bg-surface-muted'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Session selector */}
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
          <option value="">All sessions (or select one…)</option>
          {sessions?.map((s) => (
            <option key={s.id} value={s.id}>
              {s.model_name} — {s.created_at.slice(0, 10)} — ASR {(s.asr * 100).toFixed(1)}%
            </option>
          ))}
        </select>
      </div>

      {/* Compare mode */}
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
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">
                  Attack Text
                </th>
                <th className="text-right px-3 py-2 font-medium text-text-secondary border-b border-border">
                  #Total
                </th>
                <th className="text-right px-3 py-2 font-medium text-text-secondary border-b border-border">
                  #Success
                </th>
                <th className="text-right px-3 py-2 font-medium text-text-secondary border-b border-border">
                  #Safe
                </th>
              </tr>
            </thead>
            <tbody>
              {grouped.map((g) => (
                <tr
                  key={g.attack_text}
                  onClick={() =>
                    setSelectedGroup(
                      selectedGroup?.attack_text === g.attack_text ? null : g,
                    )
                  }
                  className={`border-b border-border cursor-pointer transition-colors ${
                    selectedGroup?.attack_text === g.attack_text
                      ? 'bg-accent-subtle'
                      : 'hover:bg-surface-muted'
                  }`}
                >
                  <td className="px-3 py-2 text-text-primary">
                    {g.attack_text.slice(0, 100)}
                    {g.attack_text.length > 100 ? '…' : ''}
                  </td>
                  <td className="px-3 py-2 text-right text-text-secondary font-mono">
                    {g.total}
                  </td>
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
                <RunCard
                  run={comparisonPair.best}
                  label="All runs share the same outcome — showing highest scorer"
                />
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

      {/* All runs mode */}
      {mode === 'all' && runs && runs.items.length > 0 && (
        <div>
          <table className="w-full text-sm border-collapse mb-3">
            <thead>
              <tr className="bg-surface-muted">
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">
                  Attack Text
                </th>
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">
                  Category
                </th>
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">
                  Strategy
                </th>
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">
                  Outcome
                </th>
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">
                  Score
                </th>
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">
                  Triage
                </th>
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
                  <td className="px-3 py-2 text-text-primary">
                    {run.attack_text.slice(0, 80)}…
                  </td>
                  <td className="px-3 py-2 text-text-secondary">{labelName(run.harm_category)}</td>
                  <td className="px-3 py-2 text-text-secondary font-mono text-xs">
                    {run.strategy}
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={`text-xs font-semibold ${run.jailbreak_success ? 'text-danger' : 'text-success'}`}
                    >
                      {run.jailbreak_success ? 'Jailbreak' : 'Safe'}
                    </span>
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-text-secondary">
                    {run.classifier_score.toFixed(2)}
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={`text-xs font-semibold px-1.5 py-0.5 rounded-full ${triageBadgeClass(run.triage_tier)}`}
                    >
                      {triageLabel(run.triage_tier)}
                    </span>
                  </td>
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
        <span
          className={`text-xs px-1.5 py-0.5 rounded-full ${triageBadgeClass(run.triage_tier)}`}
        >
          {triageLabel(run.triage_tier)}
        </span>
      </div>
      <ScoreBar score={run.classifier_score} success={run.jailbreak_success} />
      <pre className="bg-surface-muted rounded p-2 text-xs font-mono whitespace-pre-wrap break-words text-text-primary max-h-36 overflow-y-auto">
        {run.attack_text}
      </pre>
      <pre className="bg-surface-muted rounded p-2 text-xs font-mono whitespace-pre-wrap break-words text-text-primary max-h-48 overflow-y-auto">
        {run.response_text}
      </pre>
      <DecisionForm runId={run.id} />
    </div>
  )
}
