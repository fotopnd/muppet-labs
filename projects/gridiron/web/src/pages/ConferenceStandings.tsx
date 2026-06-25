import { useParams, Link } from 'react-router-dom'
import { useAllConglomerates, useConglomerateStandings } from '@/api/hooks'
import type { ProgramStanding } from '@/types'

function StandingsTable({ programs, code }: { programs: ProgramStanding[]; code: string }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-text-muted text-xs border-b border-border">
          <th className="text-left py-1.5 pr-3 w-6">#</th>
          <th className="text-left py-1.5 pr-3">Program</th>
          <th className="text-right py-1.5 px-2">W</th>
          <th className="text-right py-1.5 px-2">L</th>
          <th className="text-right py-1.5 pl-2">ELO</th>
        </tr>
      </thead>
      <tbody>
        {programs.map((p, i) => (
          <tr key={p.id} className="border-b border-border/40">
            <td className="py-1.5 pr-3 text-text-muted tabular-nums">{i + 1}</td>
            <td className="py-1.5 pr-3">
              <Link
                to={`/conference/${code}/programs/${p.id}`}
                className="hover:text-accent transition-colors flex items-center gap-1.5"
              >
                <span>{p.emoji}</span>
                <span>{p.name}</span>
              </Link>
            </td>
            <td className="py-1.5 px-2 text-right tabular-nums">{p.wins}</td>
            <td className="py-1.5 px-2 text-right tabular-nums">{p.losses}</td>
            <td className="py-1.5 pl-2 text-right tabular-nums text-text-muted">
              {Math.round(p.elo)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default function ConferenceStandings() {
  const { code } = useParams<{ code: string }>()
  const { data: allConglomerates } = useAllConglomerates()
  const conglomerate = allConglomerates?.find(c => c.code === code)
  const { data: standings, isLoading } = useConglomerateStandings(conglomerate?.id ?? 0, {
    enabled: !!conglomerate?.id,
  })

  if (isLoading) return <div className="p-6 text-text-muted">Loading...</div>
  if (!standings) return null

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-6">
      <section>
        <h2 className="text-xs font-semibold uppercase tracking-widest text-text-muted mb-2">
          Tier 1
        </h2>
        <StandingsTable programs={standings.tier1} code={code!} />
      </section>
      <section>
        <h2 className="text-xs font-semibold uppercase tracking-widest text-text-muted mb-2">
          Tier 2
        </h2>
        <StandingsTable programs={standings.tier2} code={code!} />
      </section>
    </div>
  )
}
