import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useCurrentSchedule, useTickerStream } from '@/api/hooks'
import type { SsePlayEvent, ScheduleGame } from '@/types'

type LiveScore = { home_score: number; away_score: number; quarter: number }

export default function TickerBar() {
  const { data: schedule } = useCurrentSchedule()
  // game_id → latest live score from SSE
  const [scores, setScores] = useState<Map<number, LiveScore>>(new Map())

  useTickerStream((e: SsePlayEvent) => {
    setScores((prev) => {
      const next = new Map(prev)
      next.set(e.game_id, {
        home_score: e.score_home,
        away_score: e.score_away,
        quarter: e.quarter,
      })
      return next
    })
  })

  const liveGameIds = Array.from(scores.keys())
  if (liveGameIds.length === 0) {
    return (
      <div className="bg-surface border-b border-border px-4 py-1.5 text-xs text-text-muted">
        No games live right now
      </div>
    )
  }

  // Build a lookup from game_id → ScheduleGame for team names
  const gameMap = new Map<number, ScheduleGame>()
  schedule?.games.forEach((g) => gameMap.set(g.game_id, g))

  return (
    <div className="bg-surface border-b border-border overflow-x-auto">
      <div className="flex gap-4 px-4 py-1.5 w-max">
        {liveGameIds.map((gid) => {
          const live = scores.get(gid)
          const game = gameMap.get(gid)
          if (!live) return null
          return (
            <Link
              key={gid}
              to={`/games/${gid}`}
              className="flex items-center gap-2 text-xs whitespace-nowrap hover:text-accent transition-colors"
            >
              <span className="text-accent text-[10px] font-semibold">Q{live.quarter}</span>
              {game ? (
                <>
                  <span>{game.home_emoji} {live.home_score}</span>
                  <span className="text-text-muted">–</span>
                  <span>{live.away_score} {game.away_emoji}</span>
                </>
              ) : (
                <span>Game {gid}: {live.home_score}–{live.away_score}</span>
              )}
            </Link>
          )
        })}
      </div>
    </div>
  )
}
