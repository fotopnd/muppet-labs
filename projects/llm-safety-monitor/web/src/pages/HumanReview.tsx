import { useState } from 'react'
import { useDecide, useEscalationQueue } from '@/api/review'
import { EscalationCard } from '@/components/EscalationCard'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Skeleton } from '@/components/Skeleton'

const PAGE_SIZE = 20

export function HumanReview() {
  const { data, isLoading, isError } = useEscalationQueue()
  const mutation = useDecide()
  const [pendingId, setPendingId] = useState<string | null>(null)
  const [page, setPage] = useState(0)
  const [decidedIds, setDecidedIds] = useState<Set<string>>(new Set())

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-48 w-full" />
        ))}
      </div>
    )
  }

  if (isError) {
    return <ErrorMessage message="Failed to load escalation queue" />
  }

  const visibleSamples = (data?.samples ?? []).filter((s) => !decidedIds.has(s.event_id))
  const pendingCount = Math.max(0, (data?.total ?? 0) - decidedIds.size)
  const totalPages = Math.max(1, Math.ceil(visibleSamples.length / PAGE_SIZE))
  const safePage = Math.min(page, totalPages - 1)
  const paginatedSamples = visibleSamples.slice(safePage * PAGE_SIZE, (safePage + 1) * PAGE_SIZE)

  function handleDecide(
    eventId: string,
    decision: 'harmful' | 'safe' | 'needs_review',
  ) {
    setDecidedIds((prev) => new Set([...prev, eventId]))
    setPendingId(eventId)
    mutation.mutate(
      { caseId: eventId, decision },
      { onSettled: () => setPendingId(null) },
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">
          Pending review:{' '}
          <span className="font-medium text-slate-800">{pendingCount}</span>
        </p>
        {totalPages > 1 && (
          <div className="flex items-center gap-2 text-sm">
            <button
              disabled={safePage === 0}
              onClick={() => setPage((p) => p - 1)}
              className="px-3 py-1 rounded border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Prev
            </button>
            <span className="text-slate-400">
              {safePage + 1} / {totalPages}
            </span>
            <button
              disabled={safePage >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1 rounded border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        )}
      </div>
      {paginatedSamples.map((item) => (
        <EscalationCard
          key={item.event_id}
          item={item}
          isPending={pendingId === item.event_id}
          onDecide={(decision) => handleDecide(item.event_id, decision)}
        />
      ))}
      {visibleSamples.length === 0 && (
        <p className="text-center text-slate-400 py-12 font-sans text-sm">
          No pending cases.
        </p>
      )}
    </div>
  )
}
