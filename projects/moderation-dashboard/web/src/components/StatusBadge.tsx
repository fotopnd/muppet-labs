type Status = 'active' | 'pending_weights' | 'live' | 'seeded'

type StatusBadgeProps = {
  status: Status
}

const CONFIG: Record<Status, { label: string; className: string }> = {
  active:          { label: 'Active',          className: 'bg-success/10 text-success' },
  pending_weights: { label: 'Pending weights', className: 'bg-warning/10 text-warning' },
  live:            { label: 'LIVE',            className: 'bg-success text-white' },
  seeded:          { label: 'Seeded',          className: 'bg-border text-text-muted' },
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const { label, className } = CONFIG[status]
  return (
    <span className={`font-data text-xs px-2 py-0.5 rounded ${className}`}>
      {label}
    </span>
  )
}
