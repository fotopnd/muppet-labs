import { ErrorMessage } from '@/components/ErrorMessage'
import { EscalationCaseRow } from '@/components/EscalationCaseRow'
import { FeedItemSkeleton } from '@/components/FeedItemSkeleton'
import { useDashboardCases } from '@/api/analytics'

const CASE_QUEUE_URL = import.meta.env.VITE_CASE_QUEUE_URL ?? 'http://localhost:8000'

export function HumanReview() {
  const { data, isLoading, isError } = useDashboardCases()

  return (
    <div className="bg-surface rounded-lg border border-border p-5">
      <h2 className="font-interface text-base font-semibold text-text-intense mb-1">
        Pending Escalations
      </h2>
      <p className="font-interface text-xs text-text-muted mb-4">
        Cases from this dashboard awaiting human review in case-queue. Opens in a new tab.
      </p>

      {isError ? (
        <ErrorMessage
          title="Case queue unavailable"
          body="Retrying automatically…"
        />
      ) : isLoading ? (
        <ul>
          {[0, 1, 2].map(i => (
            <FeedItemSkeleton key={i} />
          ))}
        </ul>
      ) : !data || data.items.length === 0 ? (
        <p className="font-interface text-sm text-text-muted py-4 text-center">
          No pending escalations
        </p>
      ) : (
        <>
          <p className="font-interface text-xs text-text-muted mb-3">
            {data.total} pending case{data.total !== 1 ? 's' : ''}
          </p>
          <ul>
            {data.items.map(item => (
              <EscalationCaseRow
                key={item.id}
                caseItem={item}
                caseQueueUrl={CASE_QUEUE_URL}
              />
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
