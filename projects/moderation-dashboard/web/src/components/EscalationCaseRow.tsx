import type { EscalationCase } from '@/types'

type EscalationCaseRowProps = {
  caseItem: EscalationCase
  onDecide: (escalationId: string, action: 'approved' | 'rejected') => void
  isPending: boolean
}

const REASON_LABELS: Record<string, string> = {
  low_confidence: 'Low confidence',
  model_disagreement: 'Model disagreement',
}

export function EscalationCaseRow({ caseItem, onDecide, isPending }: EscalationCaseRowProps) {
  const decided = caseItem.action !== null
  const reasonLabel = REASON_LABELS[caseItem.escalation_reason] ?? caseItem.escalation_reason

  return (
    <li className="flex flex-col gap-2 py-3 border-b border-border last:border-0">
      <div className="flex items-start gap-3">
        <p className="font-interface text-sm text-text-default flex-1 min-w-0 line-clamp-2">
          {caseItem.content}
        </p>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <span className="font-data text-xs px-2 py-0.5 rounded bg-accent-subtle text-accent">
            {caseItem.category}
          </span>
          <span className="font-data text-xs px-2 py-0.5 rounded bg-warning/10 text-warning">
            {reasonLabel}
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <span className="font-interface text-xs text-text-muted">
          {new Date(caseItem.created_at).toLocaleTimeString()}
          {caseItem.confidence_max !== null &&
            ` · conf ${caseItem.confidence_max.toFixed(2)}`}
        </span>

        {decided ? (
          <span
            className={[
              'font-data text-xs px-2 py-0.5 rounded font-medium',
              caseItem.action === 'approved'
                ? 'bg-success/10 text-success'
                : 'bg-danger/10 text-danger',
            ].join(' ')}
          >
            {caseItem.action === 'approved' ? 'Approved' : 'Rejected'}
          </span>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={() => onDecide(caseItem.id, 'approved')}
              disabled={isPending}
              className="font-interface text-xs px-3 py-1 rounded bg-success/10 text-success hover:bg-success/20 disabled:opacity-40 transition-colors"
            >
              Approve
            </button>
            <button
              onClick={() => onDecide(caseItem.id, 'rejected')}
              disabled={isPending}
              className="font-interface text-xs px-3 py-1 rounded bg-danger/10 text-danger hover:bg-danger/20 disabled:opacity-40 transition-colors"
            >
              Reject
            </button>
          </div>
        )}
      </div>
    </li>
  )
}
