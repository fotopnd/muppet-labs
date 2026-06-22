import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  useAllConglomerates,
  useConglomerateStandings,
  useWeekSchedule,
  useTickerScoreboard,
} from '@/api/hooks'
import GameCard from '@/components/GameCard'

export default function ConferenceSchedule() {
  const { code, week } = useParams<{ code: string; week: string }>()
  const weekNum = Number(week) || 1
  const { data: allConglomerates } = useAllConglomerates()
  const conglomerate = allConglomerates?.find(c => c.code === code)
  const { data: standings } = useConglomerateStandings(conglomerate?.id ?? 0, {
    enabled: !!conglomerate?.id,
  })
  const { data: schedule } = useWeekSchedule(weekNum)
  const scoreboard = useTickerScoreboard()
  const [revealedGames, setRevealedGames] = useState<Set<number>>(new Set())

  const allIds = new Set([
    ...(standings?.tier1.map(p => p.id) ?? []),
    ...(standings?.tier2.map(p => p.id) ?? []),
  ])

  const games = (schedule?.games ?? []).filter(
    g => allIds.has(g.home_program_id) || allIds.has(g.away_program_id),
  )

  function reveal(gameId: number) {
    setRevealedGames(prev => new Set([...prev, gameId]))
  }

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-text-muted">
          Week {weekNum}
        </h2>
        <div className="flex gap-4 text-sm text-text-muted">
          {weekNum > 1 && (
            <Link
              to={`/conference/${code}/schedule/week/${weekNum - 1}`}
              className="hover:text-text-primary transition-colors"
            >
              ← Week {weekNum - 1}
            </Link>
          )}
          {weekNum < 26 && (
            <Link
              to={`/conference/${code}/schedule/week/${weekNum + 1}`}
              className="hover:text-text-primary transition-colors"
            >
              Week {weekNum + 1} →
            </Link>
          )}
        </div>
      </div>
      {games.length === 0 ? (
        <p className="text-text-muted text-sm">No games this week.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {games.map(g => (
            <GameCard
              key={g.game_id}
              game={g}
              liveScore={scoreboard.get(g.game_id)}
              revealed={g.status !== 'complete' || revealedGames.has(g.game_id)}
              onReveal={() => reveal(g.game_id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
