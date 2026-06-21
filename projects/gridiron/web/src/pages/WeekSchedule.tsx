import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useWeekSchedule, useTickerScoreboard, useLiveLeaders } from '@/api/hooks'
import GameCard from '@/components/GameCard'
import type { LiveLeader } from '@/types'

const MIN_WEEK = 1
const MAX_WEEK = 26

export default function WeekSchedule() {
  const { week: weekParam } = useParams<{ week: string }>()
  const week = parseInt(weekParam ?? '1', 10)
  const navigate = useNavigate()
  const { data, isLoading, isError } = useWeekSchedule(week)
  const scoreboard = useTickerScoreboard()
  const [revealedGames, setRevealedGames] = useState<Set<number>>(new Set())

  const hasLive = data?.games.some((g) => g.status === 'live') ?? false
  const { data: leaders } = useLiveLeaders(hasLive)

  if (isLoading) return <div className="p-6 text-text-muted">Loading...</div>
  if (isError) return <div className="p-6 text-text-muted">Failed to load week {week}.</div>

  function reveal(gameId: number) {
    setRevealedGames((prev) => new Set([...prev, gameId]))
  }

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

      {hasLive && leaders && (leaders.rushers.length > 0 || leaders.receivers.length > 0) && (
        <div className="bg-surface border border-border rounded-lg p-3 mb-4 grid grid-cols-2 gap-3">
          <LiveLeadersCol label="Rush Leaders" entries={leaders.rushers} />
          <LiveLeadersCol label="Rec Leaders" entries={leaders.receivers} />
        </div>
      )}

      {!data || data.games.length === 0 ? (
        <p className="text-text-muted text-center py-8">No games found for week {week}.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {data.games.map((g) => (
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

function LiveLeadersCol({ label, entries }: { label: string; entries: LiveLeader[] }) {
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted mb-1.5">{label}</p>
      {entries.slice(0, 5).map((e) => (
        <div key={`${e.player_id}_${e.game_id}`} className="flex justify-between text-[11px] mb-0.5">
          <span className="truncate text-text-muted">{e.program_emoji} {e.name}</span>
          <span className="tabular-nums shrink-0 ml-2">{e.yards}y</span>
        </div>
      ))}
    </div>
  )
}
