import { useEscalationQueue } from '@/api/review'
import { ErrorMessage } from '@/components/ErrorMessage'
import { EscalationReasonBadge } from '@/components/EscalationReasonBadge'
import { Skeleton } from '@/components/Skeleton'
import type { EscalationReason } from '@/types'

export function HumanReview() {
  const { data, isLoading, isError } = useEscalationQueue()

  if (isLoading) return <Skeleton className="h-40 w-full" />
  if (isError) return <ErrorMessage message="Failed to load escalation queue" />

  const samples = data?.samples ?? []

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-500">
        Escalated events pending review:{' '}
        <span className="font-medium text-gray-800">{data?.total ?? 0}</span>
      </p>
      {samples.map((s) => (
        <div key={s.event_id} className="border border-gray-200 rounded-lg p-4 space-y-2">
          <div className="flex items-center gap-2">
            <EscalationReasonBadge reason={null as EscalationReason | null} />
            <span className="text-xs text-gray-500 font-mono">{s.event_id.slice(0, 8)}…</span>
          </div>
          <p className="text-sm text-gray-800">{s.prompt_text}</p>
          <div className="flex gap-3 text-xs text-gray-500">
            <span>Pair: {s.pair_label === 1 ? '⚠ Unsafe' : s.pair_label === 0 ? '✓ Safe' : '—'}</span>
            {(s.taxonomy_labels?.length ?? 0) > 0 && (
              <span>Categories: {s.taxonomy_labels!.join(', ')}</span>
            )}
          </div>
        </div>
      ))}
      {samples.length === 0 && (
        <p className="text-center text-gray-400 py-12">No events in the review queue.</p>
      )}
    </div>
  )
}
