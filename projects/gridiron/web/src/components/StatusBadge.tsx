import type { GameStatus } from '@/types'

export default function StatusBadge({ status }: { status: GameStatus }) {
  if (status === 'live') {
    return (
      <span className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-semibold bg-accent/20 text-accent">
        <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
        LIVE
      </span>
    )
  }
  if (status === 'complete') {
    return (
      <span className="rounded px-2 py-0.5 text-xs font-semibold bg-accent-blue/20 text-accent-blue">
        Final
      </span>
    )
  }
  return (
    <span className="rounded px-2 py-0.5 text-xs font-semibold bg-white/10 text-text-muted">
      Scheduled
    </span>
  )
}
