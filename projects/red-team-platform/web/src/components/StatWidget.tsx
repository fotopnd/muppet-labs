type StatWidgetProps = {
  label: string
  value: string | number
  subLabel?: string
  loading?: boolean
}

export function StatWidget({ label, value, subLabel, loading = false }: StatWidgetProps) {
  return (
    <div className="bg-surface rounded-lg border border-border p-4">
      <p className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-1">{label}</p>
      {loading ? (
        <div className="h-8 bg-surface-muted rounded animate-pulse mt-1" />
      ) : (
        <p className="text-3xl font-mono font-semibold text-text-primary leading-none">{value}</p>
      )}
      {subLabel && !loading && (
        <p className="text-xs text-text-muted mt-1 truncate" title={subLabel}>{subLabel}</p>
      )}
    </div>
  )
}
