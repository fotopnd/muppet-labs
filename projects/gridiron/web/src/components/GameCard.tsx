import { Link } from 'react-router-dom'
import type { ScheduleGame } from '@/types'
import StatusBadge from './StatusBadge'

export default function GameCard({ game }: { game: ScheduleGame }) {
  const isPlayed = game.status !== 'scheduled'
  return (
    <Link
      to={`/games/${game.game_id}`}
      className="block bg-surface border border-border rounded-lg p-4 hover:border-accent/40 transition-colors"
    >
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
        {isPlayed && (
          <div className="text-right shrink-0">
            <div className="text-lg font-bold tabular-nums">{game.home_score}</div>
            <div className="text-lg font-bold tabular-nums">{game.away_score}</div>
          </div>
        )}
      </div>
    </Link>
  )
}
