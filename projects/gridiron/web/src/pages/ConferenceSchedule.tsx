import { useParams, Link } from 'react-router-dom'
import {
  useAllConglomerates,
  useConglomerateStandings,
  useCurrentSchedule,
  useWeekSchedule,
  useTickerGameState,
} from '@/api/hooks'
import ScoreboardWidget from '@/components/ScoreboardWidget'

export default function ConferenceSchedule() {
  const { code, week } = useParams<{ code: string; week?: string }>()
  const weekNum = week ? Number(week) : undefined

  const { data: allConglomerates } = useAllConglomerates()
  const conglomerate = allConglomerates?.find(c => c.code === code)
  const { data: standings } = useConglomerateStandings(conglomerate?.id ?? 0, {
    enabled: !!conglomerate?.id,
  })

  const { data: currentSched } = useCurrentSchedule()
  const { data: explicitSched } = useWeekSchedule(weekNum ?? 0, { enabled: !!weekNum })
  const schedule = weekNum ? explicitSched : currentSched
  const displayWeek = schedule?.week ?? weekNum

  const tickerState = useTickerGameState()

  const allIds = new Set([
    ...(standings?.tier1.map(p => p.id) ?? []),
    ...(standings?.tier2.map(p => p.id) ?? []),
  ])
  const ready = allIds.size > 0 && !!schedule

  const games = ready
    ? schedule!.games.filter(g => allIds.has(g.home_program_id) || allIds.has(g.away_program_id))
    : []

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-text-muted">
          {displayWeek ? `Week ${displayWeek}` : 'Schedule'}
        </h2>
        <div className="flex gap-4 text-sm text-text-muted">
          {displayWeek && displayWeek > 1 && (
            <Link
              to={`/conference/${code}/schedule/week/${displayWeek - 1}`}
              className="hover:text-text-primary transition-colors"
            >
              ← Week {displayWeek - 1}
            </Link>
          )}
          {displayWeek && displayWeek < 26 && (
            <Link
              to={`/conference/${code}/schedule/week/${displayWeek + 1}`}
              className="hover:text-text-primary transition-colors"
            >
              Week {displayWeek + 1} →
            </Link>
          )}
        </div>
      </div>
      {!ready ? (
        <p className="text-text-muted text-sm">Loading...</p>
      ) : games.length === 0 ? (
        <p className="text-text-muted text-sm">No games this week.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {games.map(g => (
            <ScoreboardWidget
              key={g.game_id}
              game={g}
              liveState={tickerState.get(g.game_id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
