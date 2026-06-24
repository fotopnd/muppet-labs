import { useParams, Link } from 'react-router-dom'
import { useCoach } from '@/api/hooks'
import type { CoachSeasonRow } from '@/types'

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="text-right text-[10px] text-text-muted font-medium py-1.5 px-2 whitespace-nowrap first:text-left">
      {children}
    </th>
  )
}
function Td({ children }: { children: React.ReactNode }) {
  return <td className="text-right tabular-nums py-1.5 px-2 first:text-left">{children}</td>
}

function SeasonRow({ s }: { s: CoachSeasonRow }) {
  return (
    <tr className="border-t border-border">
      <Td>{s.season}</Td>
      <Td>{s.program_emoji} {s.program_name}</Td>
      <Td>{s.wins}</Td>
      <Td>{s.losses}</Td>
      <Td>{s.win_pct.toFixed(3)}</Td>
      <Td>{s.off_yards.toLocaleString()}</Td>
      <Td>{s.pass_yards.toLocaleString()}</Td>
      <Td>{s.rush_yards.toLocaleString()}</Td>
      <Td>{s.def_yards_allowed.toLocaleString()}</Td>
      <Td>{s.sacks}</Td>
      <Td>{s.interceptions}</Td>
    </tr>
  )
}

export default function CoachPage() {
  const { coachId: idParam } = useParams<{ coachId: string }>()
  const coachId = parseInt(idParam ?? '0', 10)
  const { data: coach, isLoading, isError } = useCoach(coachId)

  if (isLoading) return <div className="p-6 text-text-muted">Loading...</div>
  if (isError || !coach) return <div className="p-6 text-text-muted">Coach not found.</div>

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-4">
      {/* Header */}
      <div className="bg-surface border border-border rounded-lg p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-text-muted text-xs font-semibold uppercase tracking-widest mb-1">
              {coach.role}
            </div>
            <h1 className="text-2xl font-bold">{coach.first_name} {coach.last_name}</h1>
            <Link
              to={`/conference/${coach.conglomerate_code}/programs/${coach.program_id}`}
              className="text-sm text-text-muted hover:text-accent transition-colors mt-0.5 inline-block"
            >
              {coach.program_emoji} {coach.program_name}
            </Link>
          </div>
          <span className="text-4xl select-none">{coach.program_emoji}</span>
        </div>
      </div>

      {/* Season history */}
      {coach.seasons.length === 0 ? (
        <div className="bg-surface border border-border rounded-lg p-4 text-text-muted text-sm">
          No completed seasons yet.
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-lg p-4">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-text-muted mb-3">
            Season History
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <Th>Season</Th>
                  <Th>School</Th>
                  <Th>W</Th>
                  <Th>L</Th>
                  <Th>W%</Th>
                  <Th>Off Yds</Th>
                  <Th>Pass Yds</Th>
                  <Th>Rush Yds</Th>
                  <Th>Def Yds</Th>
                  <Th>Sacks</Th>
                  <Th>INT</Th>
                </tr>
              </thead>
              <tbody>
                {coach.seasons.map((s) => (
                  <SeasonRow key={s.season} s={s} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
