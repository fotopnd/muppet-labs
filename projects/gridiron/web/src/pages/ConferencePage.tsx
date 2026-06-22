import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  useAllConglomerates,
  useConglomerateStandings,
  useCurrentSchedule,
  useTickerGameState,
  useTickerScoreboard,
} from '@/api/hooks'
import GameCard from '@/components/GameCard'
import ScoreboardWidget from '@/components/ScoreboardWidget'
import type { ScheduleGame } from '@/types'

export default function ConferencePage() {
  const { code } = useParams<{ code: string }>()
  const { data: allConglomerates, isLoading: confLoading } = useAllConglomerates()
  const conglomerate = allConglomerates?.find(c => c.code === code)

  const { data: standings } = useConglomerateStandings(conglomerate?.id ?? 0, {
    enabled: !!conglomerate?.id,
  })
  const { data: schedule } = useCurrentSchedule()
  const tickerState = useTickerGameState()
  const scoreboard = useTickerScoreboard()
  const [revealedGames, setRevealedGames] = useState<Set<number>>(new Set())

  if (confLoading) return <div className="p-6 text-text-muted">Loading...</div>
  if (!conglomerate) return <div className="p-6 text-text-muted">Conference not found.</div>

  const tier1Ids = new Set(standings?.tier1.map(p => p.id) ?? [])
  const tier2Ids = new Set(standings?.tier2.map(p => p.id) ?? [])
  const allIds = new Set([...tier1Ids, ...tier2Ids])

  const conferenceGames = (schedule?.games ?? []).filter(
    g => allIds.has(g.home_program_id) || allIds.has(g.away_program_id),
  )

  function gameTier(g: ScheduleGame): 1 | 2 {
    return tier1Ids.has(g.home_program_id) || tier1Ids.has(g.away_program_id) ? 1 : 2
  }

  const tier1Games = conferenceGames.filter(g => gameTier(g) === 1)
  const tier2Games = conferenceGames.filter(g => gameTier(g) === 2)

  function reveal(gameId: number) {
    setRevealedGames(prev => new Set([...prev, gameId]))
  }

  return (
    <div className="pb-8">
      {/* Conference header */}
      <div
        className="px-4 md:px-6 py-5"
        style={{ backgroundColor: conglomerate.primary_color }}
      >
        <div className="max-w-5xl mx-auto">
          <p className="text-xs font-semibold uppercase tracking-widest text-white/70 mb-1">
            NAFCA · {conglomerate.code}
          </p>
          <h1 className="text-2xl font-bold text-white">{conglomerate.full_name}</h1>
          <p className="text-sm text-white/70 mt-0.5">{conglomerate.network} · {conglomerate.region}</p>
        </div>
      </div>

      <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-8">
        <TierSection
          title="Tier 1"
          games={tier1Games}
          tickerState={tickerState}
          scoreboard={scoreboard}
          revealedGames={revealedGames}
          onReveal={reveal}
        />
        <TierSection
          title="Tier 2"
          games={tier2Games}
          tickerState={tickerState}
          scoreboard={scoreboard}
          revealedGames={revealedGames}
          onReveal={reveal}
        />

        <div className="flex gap-4 text-sm text-text-muted pt-2 border-t border-border">
          <Link to={`/conference/${code}/standings`} className="hover:text-text-primary transition-colors">→ Full Standings</Link>
          <Link to={`/conference/${code}/stats`} className="hover:text-text-primary transition-colors">→ Season Leaders</Link>
        </div>
      </div>
    </div>
  )
}

function TierSection({
  title, games, tickerState, scoreboard, revealedGames, onReveal,
}: {
  title: string
  games: ScheduleGame[]
  tickerState: Map<number, import('@/types').SsePlayEvent>
  scoreboard: Map<number, import('@/types').LiveScore>
  revealedGames: Set<number>
  onReveal: (id: number) => void
}) {
  if (games.length === 0) return null

  const liveGames = games.filter(g => g.status === 'live')
  const otherGames = games.filter(g => g.status !== 'live')

  return (
    <section>
      <h2 className="text-xs font-semibold uppercase tracking-widest text-text-muted mb-3">{title}</h2>

      {liveGames.length > 0 && (
        <div className="mb-4">
          <p className="text-[10px] uppercase tracking-wider text-accent mb-2">Live Now</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {liveGames.map(g => (
              <ScoreboardWidget
                key={g.game_id}
                game={g}
                liveState={tickerState.get(g.game_id)}
              />
            ))}
          </div>
        </div>
      )}

      {otherGames.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {otherGames.map(g => (
            <GameCard
              key={g.game_id}
              game={g}
              liveScore={scoreboard.get(g.game_id)}
              revealed={g.status !== 'complete' || revealedGames.has(g.game_id)}
              onReveal={() => onReveal(g.game_id)}
            />
          ))}
        </div>
      )}
    </section>
  )
}
