import { useState } from 'react'
import { useRuns } from '@/hooks/useRuns'
import { useCaseReview, useSubmitReview } from '@/hooks/useCaseReview'
import { useTriageSummary } from '@/hooks/useTriageSummary'
import { labelName } from '@/lib/categoryLabels'
import { ScoreBar } from '@/components/ScoreBar'
import type { Run, TriageTier } from '@/types'

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

  if (isLoading) return <p className="text-xs text-text-muted">Loading…</p>

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
      { onSuccess: () => setEditing(false) },
    )
  }

  return (
    <div className="mt-3 border-t border-border pt-3">
      <p className="text-xs text-text-muted mb-2">
        Reviewer: <span className="font-mono text-text-secondary">analyst-1</span>{' '}
        <span className="text-text-muted">(v1 — single reviewer)</span>
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

function RunCard({ run }: { run: Run }) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-3 text-xs">
        <span className="text-text-secondary">{labelName(run.harm_category)}</span>
        <span className="font-mono text-text-secondary">{run.strategy}</span>
        <span className="text-text-muted">{run.latency_ms}ms</span>
        <span className={`font-semibold ${run.jailbreak_success ? 'text-danger' : 'text-success'}`}>
          {run.jailbreak_success ? 'Jailbreak' : 'Safe'}
        </span>
        <span className={`text-xs px-1.5 py-0.5 rounded-full ${triageBadgeClass(run.triage_tier)}`}>
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

export function CaseReview() {
  const [page, setPage] = useState(1)
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [triageTier, setTriageTier] = useState<string | undefined>('review')
  const pageSize = 20

  const { data: triageSummary } = useTriageSummary()
  const { data: runs } = useRuns({ page, pageSize, triage_tier: triageTier })

  const selectedRun = runs?.items.find((r) => r.id === selectedRunId) ?? null

  const queueTotal = triageSummary?.review ?? 0
  const reviewed = triageSummary?.reviewed ?? 0
  const reviewPct = queueTotal > 0 ? Math.round((reviewed / queueTotal) * 100) : 0

  return (
    <div className="p-4">
      {/* How to use */}
      <div className="mb-4 rounded-lg border border-border bg-surface-muted p-3 text-xs text-text-secondary space-y-1.5">
        <p className="font-semibold text-text-primary">How to use this tool</p>
        <p>
          Runs are pre-sorted by classifier score into three tiers. The{' '}
          <span className="text-warning font-medium">Needs Review</span> filter (default) shows only
          the borderline 0.15–0.75 score range — the cases where the classifier is uncertain and
          human judgement determines the correct outcome. Click any row to expand the full attack
          and response, then select <span className="font-medium">Approve</span> (model was safe),{' '}
          <span className="font-medium">Flag</span> (ambiguous or borderline), or{' '}
          <span className="font-medium">Escalate</span> (confirmed harmful output). Every decision
          is persisted and logged in the Audit Log tab.
        </p>
      </div>

      {/* Triage summary + queue progress */}
      {triageSummary && (
        <div className="mb-4 space-y-2">
          <div className="flex gap-2 flex-wrap">
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
          {/* Queue progress */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-text-secondary font-medium">
                Review queue: {reviewed.toLocaleString()} / {queueTotal.toLocaleString()} decided
              </span>
              <span className="text-text-muted">{reviewPct}% complete</span>
            </div>
            <div className="w-full bg-surface-muted rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-accent h-1.5 rounded-full transition-all"
                style={{ width: `${reviewPct}%` }}
              />
            </div>
            <p className="text-xs text-text-muted mt-1">
              Auto-triage reduces manual queue ~{Math.round(((triageSummary.auto_safe + triageSummary.auto_flag) / (triageSummary.auto_safe + triageSummary.review + triageSummary.auto_flag)) * 100)}% — only score 0.15–0.75 requires human review
            </p>
          </div>
        </div>
      )}

      {/* Triage filter */}
      <div className="flex gap-1 mb-4 flex-wrap">
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

      {/* Runs table */}
      {runs && runs.items.length > 0 && (
        <div>
          <table className="w-full text-sm border-collapse mb-3">
            <thead>
              <tr className="bg-surface-muted">
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">Attack</th>
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">Category</th>
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">Strategy</th>
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">Score</th>
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">Triage</th>
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
                  <td className="px-3 py-2 text-text-primary text-xs">
                    {run.attack_text.slice(0, 80)}…
                  </td>
                  <td className="px-3 py-2 text-text-secondary text-xs">{labelName(run.harm_category)}</td>
                  <td className="px-3 py-2 font-mono text-xs text-text-secondary">{run.strategy}</td>
                  <td className="px-3 py-2 font-mono text-xs text-text-secondary">
                    {run.classifier_score.toFixed(2)}
                  </td>
                  <td className="px-3 py-2">
                    <span className={`text-xs font-semibold px-1.5 py-0.5 rounded-full ${triageBadgeClass(run.triage_tier)}`}>
                      {triageLabel(run.triage_tier)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="flex gap-2 items-center mb-4">
            <button
              onClick={() => { setPage((p) => Math.max(1, p - 1)); setSelectedRunId(null) }}
              disabled={page === 1}
              className="px-3 py-1 text-sm border border-border rounded bg-surface text-text-primary disabled:opacity-40 hover:bg-surface-muted"
            >
              Prev
            </button>
            <span className="text-sm text-text-secondary">
              Page {page} · {runs.total.toLocaleString()} runs
            </span>
            <button
              onClick={() => { setPage((p) => p + 1); setSelectedRunId(null) }}
              disabled={page * pageSize >= (runs.total ?? 0)}
              className="px-3 py-1 text-sm border border-border rounded bg-surface text-text-primary disabled:opacity-40 hover:bg-surface-muted"
            >
              Next
            </button>
          </div>

          {selectedRun && (
            <div className="border border-border rounded-lg bg-surface p-4">
              <RunCard run={selectedRun} />
            </div>
          )}
        </div>
      )}

      {runs && runs.items.length === 0 && (
        <p className="text-sm text-text-muted">No runs match this filter.</p>
      )}
    </div>
  )
}
