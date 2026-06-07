function formatUplift(uplift: number): string {
  const pct = (uplift * 100).toFixed(1)
  return uplift >= 0 ? `+${pct}%` : `${pct}%`
}

type Props = {
  uplift: number | null
}

export function UpliftHero({ uplift }: Props) {
  const colorClass =
    uplift === null || uplift === 0
      ? 'text-text-muted'
      : uplift > 0
        ? 'text-success'
        : 'text-danger'

  return (
    <div className="flex flex-col items-center py-10 gap-3">
      <span className="font-interface text-xs text-text-muted uppercase tracking-widest">
        Human Uplift
      </span>

      {uplift === null ? (
        <>
          <p className="font-interface text-xl font-medium text-text-muted">Results incomplete</p>
          <p className="font-interface text-xs text-text-muted">
            Review all conditions to see uplift
          </p>
        </>
      ) : (
        <>
          <p className={`font-data text-5xl font-bold ${colorClass}`}>{formatUplift(uplift)}</p>
          <p className="font-interface text-xs text-text-muted mt-1">
            TPR(human+agent) − TPR(unaided)
          </p>
        </>
      )}
    </div>
  )
}
