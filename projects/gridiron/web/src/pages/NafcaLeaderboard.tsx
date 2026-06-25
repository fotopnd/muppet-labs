import { useState } from 'react'
import { useNafcaLeaderboard } from '@/api/hooks'
import type { ProgramEloRank } from '@/types'

type Tab = 'lifetime' | 'season'

function RankCard({ rank, program, showDelta }: { rank: number; program: ProgramEloRank; showDelta: boolean }) {
  return (
    <div className="flex items-center gap-3 p-3 bg-surface border border-border rounded-lg">
      <span className="text-text-muted text-xs w-6 text-right tabular-nums">{rank}</span>
      <span className="text-xl">{program.emoji}</span>
      <div className="flex-1 min-w-0">
        <div className="font-semibold text-sm truncate">{program.name}</div>
        <div className="text-xs text-text-muted">Tier {program.tier}</div>
      </div>
      <div className="text-right shrink-0">
        <div className="font-mono font-semibold text-sm">{Math.round(program.elo)}</div>
        {showDelta && (
          <div
            className={`text-xs font-mono ${
              program.season_delta >= 0 ? 'text-emerald-500' : 'text-red-400'
            }`}
          >
            {program.season_delta >= 0 ? '+' : ''}
            {Math.round(program.season_delta)}
          </div>
        )}
      </div>
    </div>
  )
}

export default function NafcaLeaderboard() {
  const [tab, setTab] = useState<Tab>('lifetime')
  const { data, isLoading, isError } = useNafcaLeaderboard()

  if (isLoading) return <div className="p-6 text-text-muted">Loading...</div>
  if (isError) return <div className="p-6 text-text-muted">Failed to load leaderboard.</div>
  if (!data) return null

  const programs = tab === 'lifetime' ? data.lifetime : data.season

  return (
    <div className="p-4 md:p-6 max-w-3xl mx-auto">
      <h1 className="text-xl font-bold mb-4">NAFCA Rankings</h1>
      <div className="flex gap-1 mb-4 border-b border-border">
        {(['lifetime', 'season'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors capitalize ${
              tab === t
                ? 'border-accent text-accent'
                : 'border-transparent text-text-muted hover:text-text-primary'
            }`}
          >
            {t === 'lifetime' ? 'All-Time' : 'Season'}
          </button>
        ))}
      </div>
      <div className="space-y-2">
        {programs.map((p, i) => (
          <RankCard key={p.id} rank={i + 1} program={p} showDelta={tab === 'season'} />
        ))}
      </div>
    </div>
  )
}
