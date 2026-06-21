import { Link, useNavigate } from 'react-router-dom'
import type { LiveScore, ScheduleGame } from '@/types'
import StatusBadge from './StatusBadge'

export default function GameCard({
  game, liveScore, revealed, onReveal,
}: {
  game: ScheduleGame
  liveScore?: LiveScore
  revealed?: boolean
  onReveal?: () => void
}) {
  const navigate = useNavigate()
  const href = `/games/${game.game_id}`

  const scoreBlock = (() => {
    if (game.status === 'live' && liveScore) {
      return (
        <div className="text-right shrink-0">
          <div className="text-lg font-bold tabular-nums text-accent">{liveScore.score_home}</div>
          <div className="text-lg font-bold tabular-nums text-accent">{liveScore.score_away}</div>
          <div className="text-[10px] text-text-muted mt-0.5">Q{liveScore.quarter}</div>
        </div>
      )
    }
    if (game.status === 'complete') {
      if (!revealed) {
        return (
          <div className="text-right shrink-0">
            <span className="text-[10px] text-text-muted">FINAL · reveal</span>
          </div>
        )
      }
      return (
        <div className="text-right shrink-0">
          <div className="text-lg font-bold tabular-nums">{game.home_score}</div>
          <div className="text-lg font-bold tabular-nums">{game.away_score}</div>
        </div>
      )
    }
    return null
  })()

  const inner = (
    <>
      <div className="flex items-center justify-between gap-2 mb-2">
        <StatusBadge status={game.status} />
        <span className="text-xs text-text-muted capitalize">
          {game.broadcast_slot.replace('_', ' ')}
        </span>
      </div>
      <div className="flex items-center justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 truncate">
            <span>{game.home_emoji}</span>
            <span className="text-sm truncate">{game.home_name}</span>
          </div>
          <div className="flex items-center gap-1.5 truncate mt-1">
            <span>{game.away_emoji}</span>
            <span className="text-sm truncate">{game.away_name}</span>
          </div>
        </div>
        {scoreBlock}
      </div>
    </>
  )

  // Complete + unrevealed: intercept tap to reveal, then navigate
  if (game.status === 'complete' && !revealed) {
    return (
      <div
        onClick={() => { onReveal?.(); navigate(href) }}
        className="block bg-surface border border-border rounded-lg p-4 hover:border-accent/40 transition-colors cursor-pointer"
      >
        {inner}
      </div>
    )
  }

  return (
    <Link
      to={href}
      className="block bg-surface border border-border rounded-lg p-4 hover:border-accent/40 transition-colors"
    >
      {inner}
    </Link>
  )
}
