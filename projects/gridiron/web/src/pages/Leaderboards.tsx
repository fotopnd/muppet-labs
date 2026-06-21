import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useLeaderboards } from '@/api/hooks'
import type { LeaderboardEntry } from '@/types'

type Tab = 'passers' | 'rushers' | 'receivers'
const TABS: { key: Tab; label: string }[] = [
  { key: 'passers', label: 'Passing' },
  { key: 'rushers', label: 'Rushing' },
  { key: 'receivers', label: 'Receiving' },
]

function LeaderTable({ entries }: { entries: LeaderboardEntry[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-text-muted text-xs border-b border-border">
          <th className="text-left py-2 pr-2">#</th>
          <th className="text-left py-2 pr-3">Name</th>
          <th className="text-left py-2 pr-3 hidden sm:table-cell">Program</th>
          <th className="text-right py-2 px-2">Yds</th>
          <th className="text-right py-2 px-2">TD</th>
          <th className="text-right py-2 pl-2">GP</th>
        </tr>
      </thead>
      <tbody>
        {entries.map((e, i) => (
          <tr key={e.player_id} className="border-b border-border/50">
            <td className="py-2 pr-2 text-text-muted">{i + 1}</td>
            <td className="py-2 pr-3 font-medium">{e.name}</td>
            <td className="py-2 pr-3 text-text-muted hidden sm:table-cell">{e.program_name}</td>
            <td className="py-2 px-2 text-right tabular-nums">{e.total_yards}</td>
            <td className="py-2 px-2 text-right tabular-nums">{e.tds}</td>
            <td className="py-2 pl-2 text-right tabular-nums text-text-muted">{e.games_played}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default function Leaderboards() {
  const [tab, setTab] = useState<Tab>('passers')
  const { data, isLoading, isError } = useLeaderboards()

  if (isLoading) return <div className="p-6 text-text-muted">Loading...</div>
  if (isError) return <div className="p-6 text-text-muted">Failed to load leaderboards.</div>
  if (!data) return null

  return (
    <div className="p-4 md:p-6 max-w-3xl mx-auto">
      <h1 className="text-xl font-bold mb-4">Leaderboards</h1>
      <div className="flex gap-1 mb-4 border-b border-border">
        {TABS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === key
                ? 'border-accent text-accent'
                : 'border-transparent text-text-muted hover:text-text-primary'
            }`}
          >
            {label}
          </button>
        ))}
      </div>
      <LeaderTable entries={data[tab]} />
    </div>
  )
}
