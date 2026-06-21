import { useCurrentSchedule } from '@/api/hooks'
import GameCard from '@/components/GameCard'

export default function Home() {
  const { data, isLoading, isError } = useCurrentSchedule()

  if (isLoading) return <div className="p-6 text-text-muted">Loading...</div>
  if (isError) return <div className="p-6 text-text-muted">Failed to load schedule.</div>
  if (!data) return null

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto">
      <h1 className="text-xl font-bold mb-4">Week {data.week}</h1>
      {data.games.length === 0 ? (
        <p className="text-text-muted">No games this week.</p>
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
