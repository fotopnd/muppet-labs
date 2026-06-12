import type { MetricRow } from '@/data/projects'

type MetricsTableProps = {
  rows: MetricRow[]
}

export default function MetricsTable({ rows }: MetricsTableProps) {
  if (rows.length === 0) return null

  return (
    <div className="bg-surface-muted rounded-lg p-4">
      <dl className="divide-y divide-border">
        {rows.map((row) => (
          <div
            key={row.label}
            className="flex justify-between items-baseline py-1.5 first:pt-0 last:pb-0"
          >
            <dt className="text-xs text-text-secondary">{row.label}</dt>
            <dd className="text-sm font-mono font-semibold text-text-primary tabular-nums">
              {row.value}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
