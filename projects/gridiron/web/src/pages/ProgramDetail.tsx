import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  useProgram,
  useProgramSchedule,
  useProgramRoster,
  useProgramStats,
  useProgramCoaches,
} from '@/api/hooks'
import StatusBadge from '@/components/StatusBadge'

type Tab = 'schedule' | 'roster' | 'stats' | 'staff'

const YEAR_CLASS = ['', 'Freshman', 'Sophomore', 'Junior', 'Senior'] as const

export default function ProgramDetail() {
  const { programId: idParam } = useParams<{ programId: string }>()
  const programId = parseInt(idParam ?? '0', 10)
  const [tab, setTab] = useState<Tab>('schedule')
  const { data: program, isLoading, isError } = useProgram(programId)

  if (isLoading) return <div className="p-6 text-text-muted">Loading...</div>
  if (isError || !program) return <div className="p-6 text-text-muted">Program not found.</div>

  return (
    <div className="p-4 md:p-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="bg-surface border border-border rounded-lg p-4 mb-4">
        <div className="flex items-start gap-3">
          <span className="text-4xl">{program.emoji}</span>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold">{program.name}</h1>
            <p className="text-text-muted text-sm">
              {program.city} · {program.mascot} · Tier {program.tier} · {program.conglomerate_code}
            </p>
            <div className="flex items-center gap-4 mt-2 text-sm">
              <span className="tabular-nums">{Math.round(program.elo)} Elo</span>
              <span className="text-text-muted tabular-nums">
                {program.wins}–{program.losses}
              </span>
            </div>
          </div>
          <div
            className="w-5 h-5 rounded-full shrink-0 mt-1"
            style={{ backgroundColor: program.primary_color }}
            title={program.primary_color}
          />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border mb-4">
        {(['schedule', 'roster', 'stats', 'staff'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px capitalize transition-colors ${
              tab === t
                ? 'border-accent text-accent'
                : 'border-transparent text-text-muted hover:text-text-primary'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'schedule' && <ScheduleTab programId={programId} />}
      {tab === 'roster' && <RosterTab programId={programId} />}
      {tab === 'stats' && <StatsTab programId={programId} />}
      {tab === 'staff' && <StaffTab programId={programId} />}
    </div>
  )
}

function ScheduleTab({ programId }: { programId: number }) {
  const { data, isLoading } = useProgramSchedule(programId)
  if (isLoading) return <div className="text-text-muted">Loading...</div>
  if (!data?.length) return <div className="text-text-muted">No games found.</div>
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-text-muted text-xs border-b border-border">
          <th className="text-left py-2 pr-3">Wk</th>
          <th className="text-left py-2 pr-3">Opponent</th>
          <th className="text-left py-2 pr-3">H/A</th>
          <th className="text-left py-2 pr-3">Result</th>
          <th className="text-left py-2">Slot</th>
        </tr>
      </thead>
      <tbody>
        {data.map((g) => {
          const myScore = g.is_home ? g.home_score : g.away_score
          const oppScore = g.is_home ? g.away_score : g.home_score
          const result =
            g.status === 'complete'
              ? myScore > oppScore
                ? `W ${myScore}–${oppScore}`
                : `L ${myScore}–${oppScore}`
              : g.status === 'live'
                ? `${myScore}–${oppScore}`
                : '—'
          return (
            <tr key={g.game_id} className="border-b border-border/50">
              <td className="py-2 pr-3 text-text-muted">{g.week}</td>
              <td className="py-2 pr-3">
                <Link to={`/games/${g.game_id}`} className="hover:text-accent transition-colors flex items-center gap-1">
                  <span>{g.opponent_emoji}</span> {g.opponent_name}
                </Link>
              </td>
              <td className="py-2 pr-3 text-text-muted">{g.is_home ? 'H' : 'A'}</td>
              <td className="py-2 pr-3 tabular-nums">
                <StatusBadge status={g.status} />
                {g.status !== 'scheduled' && (
                  <span className="ml-2 text-xs">{result}</span>
                )}
              </td>
              <td className="py-2 text-text-muted text-xs capitalize">
                {g.broadcast_slot.replace('_', ' ')}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

function RosterTab({ programId }: { programId: number }) {
  const { data, isLoading } = useProgramRoster(programId)
  if (isLoading) return <div className="text-text-muted">Loading...</div>
  if (!data?.length) return <div className="text-text-muted">No roster data.</div>

  // Group by position
  const byPos = new Map<string, typeof data>()
  for (const p of data) {
    const group = byPos.get(p.position) ?? []
    group.push(p)
    byPos.set(p.position, group)
  }

  return (
    <div className="space-y-4">
      {[...byPos.entries()].map(([pos, players]) => (
        <div key={pos}>
          <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1">
            {pos}
          </h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-text-muted text-xs border-b border-border">
                <th className="text-left py-1 pr-3">#</th>
                <th className="text-left py-1 pr-3">Name</th>
                <th className="text-left py-1">Yr</th>
              </tr>
            </thead>
            <tbody>
              {players.map((p) => (
                <tr key={p.player_id} className="border-b border-border/30">
                  <td className="py-1 pr-3 text-text-muted">{p.jersey_num}</td>
                  <td className="py-1 pr-3">
                    <Link to={`/players/${p.player_id}`} className="hover:text-accent transition-colors">
                      {p.first_name} {p.last_name}
                    </Link>
                  </td>
                  <td className="py-1 text-text-muted">{YEAR_CLASS[p.year] ?? p.year}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  )
}

function StatsTab({ programId }: { programId: number }) {
  const { data, isLoading } = useProgramStats(programId)
  if (isLoading) return <div className="text-text-muted">Loading...</div>
  if (!data) return null

  const isEmpty = !data.passers.length && !data.rushers.length && !data.receivers.length
  if (isEmpty) return <div className="text-text-muted">No stats yet — check back after games complete.</div>

  return (
    <div className="space-y-6">
      {data.passers.length > 0 && (
        <StatGroup label="Passing" entries={data.passers} />
      )}
      {data.rushers.length > 0 && (
        <StatGroup label="Rushing" entries={data.rushers} />
      )}
      {data.receivers.length > 0 && (
        <StatGroup label="Receiving" entries={data.receivers} />
      )}
    </div>
  )
}

function StatGroup({
  label,
  entries,
}: {
  label: string
  entries: { player_id: number; name: string; total_yards: number; tds: number; games_played: number }[]
}) {
  return (
    <div>
      <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">{label}</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-text-muted text-xs border-b border-border">
            <th className="text-left py-1 pr-3">Name</th>
            <th className="text-right py-1 px-2">Yds</th>
            <th className="text-right py-1 px-2">TD</th>
            <th className="text-right py-1 pl-2">GP</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e) => (
            <tr key={e.player_id} className="border-b border-border/30">
              <td className="py-1 pr-3">{e.name}</td>
              <td className="py-1 px-2 text-right tabular-nums">{e.total_yards}</td>
              <td className="py-1 px-2 text-right tabular-nums">{e.tds}</td>
              <td className="py-1 pl-2 text-right tabular-nums text-text-muted">{e.games_played}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const ROLE_ORDER = ['HC', 'OC', 'DC', 'ST']

function StaffTab({ programId }: { programId: number }) {
  const { data, isLoading } = useProgramCoaches(programId)
  if (isLoading) return <div className="text-text-muted">Loading...</div>
  if (!data?.length) return <div className="text-text-muted">No coaching staff found.</div>

  const sorted = [...data].sort((a, b) => {
    const ai = ROLE_ORDER.indexOf(a.role)
    const bi = ROLE_ORDER.indexOf(b.role)
    const aOrder = ai === -1 ? ROLE_ORDER.length : ai
    const bOrder = bi === -1 ? ROLE_ORDER.length : bi
    return aOrder - bOrder
  })

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-text-muted text-xs border-b border-border">
          <th className="text-left py-2 pr-3">Role</th>
          <th className="text-left py-2 pr-3">Name</th>
          <th className="text-right py-2">Rating</th>
        </tr>
      </thead>
      <tbody>
        {sorted.map((c) => (
          <tr key={c.coach_id} className="border-b border-border/30">
            <td className="py-2 pr-3 text-text-muted">{c.role}</td>
            <td className="py-2 pr-3">
              <Link to={`/coaches/${c.coach_id}`} className="hover:text-accent transition-colors">
                {c.full_name}
              </Link>
              <span className="ml-1.5 text-xs select-none">
                <span className="text-yellow-400">{'★'.repeat(c.prestige)}</span>
                <span className="text-text-muted">{'☆'.repeat(5 - c.prestige)}</span>
              </span>
            </td>
            <td className="py-2 text-right tabular-nums">{Math.round(c.rating * 100)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
