interface BiasCellProps {
  score: number | null
}

function scoreClass(score: number | null): string {
  if (score === null) return 'bg-divergence-null text-text-inverse'
  if (score < 0.15) return 'bg-divergence-low text-text-inverse'
  if (score < 0.35) return 'bg-divergence-mid text-text-inverse'
  return 'bg-divergence-high text-text-inverse'
}

export function BiasCell({ score }: BiasCellProps) {
  return (
    <td
      className={`w-20 p-2 text-center font-mono text-xs font-semibold rounded-sm ${scoreClass(score)}`}
    >
      {score === null ? '—' : score.toFixed(2)}
    </td>
  )
}
