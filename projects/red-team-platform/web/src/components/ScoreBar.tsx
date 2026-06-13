type ScoreBarProps = {
  score: number
  success: boolean
}

export function ScoreBar({ score, success }: ScoreBarProps) {
  const fillClass = success && score > 0.5
    ? 'bg-danger'
    : success
      ? 'bg-warning'
      : 'bg-accent'

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-surface-muted rounded-full overflow-hidden">
        <div
          className={`h-2 rounded-full ${fillClass}`}
          style={{ width: `${(score * 100).toFixed(1)}%` }}
        />
      </div>
      <span className="text-xs font-mono text-text-secondary w-10 text-right">
        {score.toFixed(2)}
      </span>
    </div>
  )
}
