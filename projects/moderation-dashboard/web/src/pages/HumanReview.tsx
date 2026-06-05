import { ErrorMessage } from '@/components/ErrorMessage'
import { EscalationCaseRow } from '@/components/EscalationCaseRow'
import { FeedItemSkeleton } from '@/components/FeedItemSkeleton'
import { useCases, useCreateDecision } from '@/api/cases'

export function HumanReview() {
  const { data, isLoading, isError } = useCases()
  const { mutate: decide, isPending } = useCreateDecision()

  const pending = data?.filter(c => c.action === null) ?? []
  const total = data?.length ?? 0
  const pendingCount = pending.length

  return (
    <div className="bg-surface rounded-lg border border-border p-5">
      <div className="flex items-center justify-between mb-1">
        <h2 className="font-interface text-base font-semibold text-text-intense">
          Pending Escalations
        </h2>
        {pendingCount > 0 && (
          <span className="font-data text-xs px-2 py-0.5 rounded-full bg-danger text-white">
            {pendingCount}
          </span>
        )}
      </div>
      <p className="font-interface text-xs text-text-muted mb-4">
        Events escalated by the moderation pipeline for human review. Approve or reject each case.
      </p>

      {isError ? (
        <ErrorMessage
          title="Failed to load escalations"
          body="Retrying automatically…"
        />
      ) : isLoading ? (
        <ul>
          {[0, 1, 2].map(i => (
            <FeedItemSkeleton key={i} />
          ))}
        </ul>
      ) : !data || data.length === 0 ? (
        <p className="font-interface text-sm text-text-muted py-4 text-center">
          No escalations yet
        </p>
      ) : (
        <>
          <p className="font-interface text-xs text-text-muted mb-3">
            {total} case{total !== 1 ? 's' : ''} · {pendingCount} pending
          </p>
          <ul>
            {data.map(item => (
              <EscalationCaseRow
                key={item.id}
                caseItem={item}
                onDecide={(escalationId, action) =>
                  decide({ escalationId, body: { action } })
                }
                isPending={isPending}
              />
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
