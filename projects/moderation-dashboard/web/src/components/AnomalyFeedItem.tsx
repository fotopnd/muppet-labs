import type { AnomalyFlag } from '@/types'

function relativeTime(isoString: string): string {
  const diff = (Date.now() - new Date(isoString).getTime()) / 1000
  if (diff < 60) return `${Math.floor(diff)}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  return `${Math.floor(diff / 3600)}h ago`
}

type AnomalyFeedItemProps = {
  flag: AnomalyFlag
}

export function AnomalyFeedItem({ flag }: AnomalyFeedItemProps) {
  const isHigh = Math.abs(flag.z_score) > 3

  return (
    <li className="flex items-start gap-3 py-3 border-b border-border last:border-0">
      <span className="font-data text-sm text-text-default">{flag.signal_name}</span>
      <span
        className={[
          'font-data text-xs px-2 py-0.5 rounded',
          isHigh
            ? 'bg-warning/15 text-warning'
            : 'bg-border text-text-muted',
        ].join(' ')}
      >
        Z={flag.z_score.toFixed(2)}
      </span>
      <span className="font-interface text-xs text-text-muted ml-auto whitespace-nowrap">
        {relativeTime(flag.created_at)}
      </span>
    </li>
  )
}
