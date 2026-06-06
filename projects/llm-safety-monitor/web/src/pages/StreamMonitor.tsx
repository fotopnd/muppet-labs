import { useRecentEvents } from '@/api/stream'
import { EscalationReasonBadge } from '@/components/EscalationReasonBadge'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Skeleton } from '@/components/Skeleton'
import { SourceBadge } from '@/components/SourceBadge'
import { VerdictRow } from '@/components/VerdictRow'
import type { EscalationReason, RecentEvent, SourceDataset } from '@/types'

function EventCard({ event }: { event: RecentEvent }) {
  return (
    <div className="border border-gray-200 rounded-lg p-4 space-y-2">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <SourceBadge source={event.source_dataset as SourceDataset} />
        <EscalationReasonBadge reason={event.escalation_reason as EscalationReason | null} />
      </div>
      <p className="text-sm text-gray-800 font-medium">{event.prompt_text}</p>
      {event.response_text && (
        <p className="text-sm text-gray-500 italic">{event.response_text}</p>
      )}
      {!event.response_text && (
        <p className="text-xs text-gray-400">(no response — prompt only)</p>
      )}
      <VerdictRow verdicts={event.verdicts} />
    </div>
  )
}

export function StreamMonitor() {
  const { data, isLoading, isError } = useRecentEvents(50)

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full" />
        ))}
      </div>
    )
  }

  if (isError) return <ErrorMessage message="Failed to load stream events" />

  const events = data?.events ?? []

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-500">{events.length} recent events</p>
      {events.map((event) => (
        <EventCard key={event.event_id} event={event} />
      ))}
      {events.length === 0 && (
        <p className="text-center text-gray-400 py-12">No events yet. Start the producer to stream interactions.</p>
      )}
    </div>
  )
}
