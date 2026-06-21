import { useParams, useNavigate } from 'react-router-dom'
import { useWeekSchedule } from '@/api/hooks'
import GameCard from '@/components/GameCard'

const MIN_WEEK = 1
const MAX_WEEK = 26

export default function WeekSchedule() {
  const { week: weekParam } = useParams<{ week: string }>()
  const week = parseInt(weekParam ?? '1', 10)
  const navigate = useNavigate()
  const { data, isLoading, isError } = useWeekSchedule(week)

  if (isLoading) return <div className="p-6 text-text-muted">Loading...</div>
  if (isError) return <div className="p-6 text-text-muted">Failed to load week {week}.</div>

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-4 mb-4">
        <button
          onClick={() => navigate(`/schedule/week/${week - 1}`)}
          disabled={week <= MIN_WEEK}
          className="px-3 py-1 rounded border border-border text-sm disabled:opacity-30 hover:border-accent/40 transition-colors"
        >
          ← Prev
        </button>
        <h1 className="text-xl font-bold flex-1 text-center">Week {week}</h1>
        <button
          onClick={() => navigate(`/schedule/week/${week + 1}`)}
          disabled={week >= MAX_WEEK}
          className="px-3 py-1 rounded border border-border text-sm disabled:opacity-30 hover:border-accent/40 transition-colors"
        >
          Next →
        </button>
      </div>
      {!data || data.games.length === 0 ? (
        <p className="text-text-muted text-center py-8">No games found for week {week}.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {data.games.map((g) => (
            <GameCard key={g.game_id} game={g} />
          ))}
        </div>
      )}
    </div>
  )
}
