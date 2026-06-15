import { useState } from 'react'
import { useAuditLog } from '@/hooks/useAuditLog'

const LIMIT = 50

const DECISIONS = [
  { value: '', label: 'All decisions' },
  { value: 'approve', label: 'Approved' },
  { value: 'flag', label: 'Flagged' },
  { value: 'escalate', label: 'Escalated' },
]

const REVIEWERS = [
  { value: '', label: 'All reviewers' },
  { value: 'analyst-1', label: 'analyst-1' },
]

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

export function AuditLog() {
  const [decisionFilter, setDecisionFilter] = useState('')
  const [reviewerFilter, setReviewerFilter] = useState('')
  const [offset, setOffset] = useState(0)

  const { data, isLoading, isError } = useAuditLog({
    decision: decisionFilter || undefined,
    reviewer: reviewerFilter || undefined,
    limit: LIMIT,
    offset,
  })

  const totalPages = data ? Math.ceil(data.total / LIMIT) : 0
  const currentPage = Math.floor(offset / LIMIT) + 1

  const handleFilterChange = () => {
    setOffset(0)
  }

  return (
    <div className="p-4">
      <h2 className="text-base font-semibold text-text-primary mb-3">Audit Log</h2>

      {/* How to use */}
      <div className="mb-4 rounded-lg border border-border bg-surface-muted p-3 text-xs text-text-secondary space-y-1.5">
        <p className="font-semibold text-text-primary">What this log records</p>
        <p>
          Every decision submitted in the <span className="font-medium text-text-primary">Case Review</span> tab
          is written here as an immutable entry — including edits, which append a new row rather than
          overwriting. This makes the full decision history auditable: you can see not just the current
          outcome but every reviewer action that led to it.
        </p>
        <p>
          <span className="font-medium text-text-primary">Columns:</span> timestamp of submission ·
          reviewer identity · truncated run UUID (first 8 chars) ·{' '}
          <span className="text-success font-medium">Approved</span> /{' '}
          <span className="text-warning font-medium">Flagged</span> /{' '}
          <span className="text-danger font-medium">Escalated</span> badge · optional reason text.
        </p>
        <p>
          Use the filters below to slice by decision type or reviewer. Make a decision in Case Review
          and return here to see it appear at the top of the table.
        </p>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-4 flex-wrap">
        <select
          value={decisionFilter}
          onChange={(e) => {
            setDecisionFilter(e.target.value)
            handleFilterChange()
          }}
          className="px-2 py-1 text-sm border border-border rounded bg-surface text-text-primary"
        >
          {DECISIONS.map((d) => (
            <option key={d.value} value={d.value}>
              {d.label}
            </option>
          ))}
        </select>

        <select
          value={reviewerFilter}
          onChange={(e) => {
            setReviewerFilter(e.target.value)
            handleFilterChange()
          }}
          className="px-2 py-1 text-sm border border-border rounded bg-surface text-text-primary"
        >
          {REVIEWERS.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </select>

        {data && (
          <span className="text-xs text-text-muted self-center">
            {data.total.toLocaleString()} entries
          </span>
        )}
      </div>

      {/* Loading/Error */}
      {isLoading && <p className="text-sm text-text-muted">Loading audit log…</p>}
      {isError && <p className="text-sm text-danger">Failed to load audit log.</p>}

      {/* Table */}
      {data && data.items.length === 0 && (
        <p className="text-sm text-text-muted">No audit log entries yet.</p>
      )}

      {data && data.items.length > 0 && (
        <>
          <table className="w-full text-sm border-collapse mb-4">
            <thead>
              <tr className="bg-surface-muted">
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">
                  Timestamp
                </th>
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">
                  Reviewer
                </th>
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">
                  Run
                </th>
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">
                  Decision
                </th>
                <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">
                  Reason
                </th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((entry) => (
                <tr key={entry.id} className="border-b border-border hover:bg-surface-muted">
                  <td className="px-3 py-2 text-xs text-text-muted font-mono whitespace-nowrap">
                    {new Date(entry.created_at).toLocaleString()}
                  </td>
                  <td className="px-3 py-2 text-xs text-text-secondary font-mono">
                    {entry.reviewer}
                  </td>
                  <td className="px-3 py-2 text-xs text-text-primary font-mono">
                    {entry.run_id.slice(0, 8)}…
                  </td>
                  <td className="px-3 py-2">
                    <DecisionBadge decision={entry.decision} />
                  </td>
                  <td className="px-3 py-2 text-xs text-text-secondary italic">
                    {entry.reason ?? <span className="text-text-muted">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          <div className="flex gap-2 items-center">
            <button
              onClick={() => setOffset((o) => Math.max(0, o - LIMIT))}
              disabled={offset === 0}
              className="px-3 py-1 text-sm border border-border rounded bg-surface text-text-primary disabled:opacity-40 hover:bg-surface-muted"
            >
              Prev
            </button>
            <span className="text-sm text-text-secondary">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setOffset((o) => o + LIMIT)}
              disabled={offset + LIMIT >= data.total}
              className="px-3 py-1 text-sm border border-border rounded bg-surface text-text-primary disabled:opacity-40 hover:bg-surface-muted"
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  )
}
