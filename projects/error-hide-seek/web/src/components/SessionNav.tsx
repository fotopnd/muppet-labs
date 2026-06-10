import { useNavigate } from 'react-router-dom'

type Props = {
  prevId: number | null
  nextId: number | null
  position: number
  total: number
  condition: string
}

export function SessionNav({ prevId, nextId, position, total, condition }: Props) {
  const navigate = useNavigate()

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={() => prevId !== null && navigate(`/review/${prevId}`)}
        disabled={prevId === null}
        className="px-3 py-1 font-interface text-xs rounded border border-border text-text-default hover:bg-surface disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        ← Prev
      </button>
      <span className="font-interface text-xs text-text-muted">
        {position} / {total} <span className="text-text-muted opacity-60">({condition})</span>
      </span>
      <button
        onClick={() => nextId !== null && navigate(`/review/${nextId}`)}
        disabled={nextId === null}
        className="px-3 py-1 font-interface text-xs rounded border border-border text-text-default hover:bg-surface disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        Next →
      </button>
    </div>
  )
}
