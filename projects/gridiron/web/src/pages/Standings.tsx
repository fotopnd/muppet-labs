import { Link } from 'react-router-dom'
import { useAllStandings } from '@/api/hooks'
import type { ProgramStanding } from '@/types'

function StandingsTable({ programs }: { programs: ProgramStanding[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-text-muted text-xs border-b border-border">
          <th className="text-left py-1.5 pr-3">Program</th>
          <th className="text-right py-1.5 px-2">W</th>
          <th className="text-right py-1.5 px-2">L</th>
          <th className="text-right py-1.5 pl-2">Elo</th>
        </tr>
      </thead>
      <tbody>
        {programs.map((p) => (
          <tr key={p.id} className="border-b border-border/40">
            <td className="py-1.5 pr-3">
              <Link
                to={`/programs/${p.id}`}
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

export default function Standings() {
  const results = useAllStandings()
  const isLoading = results.some((r) => r.isLoading)
  const isError = results.some((r) => r.isError)

  if (isLoading) return <div className="p-6 text-text-muted">Loading standings...</div>
  if (isError) return <div className="p-6 text-text-muted">Failed to load standings.</div>

  return (
    <div className="p-4 md:p-6 max-w-4xl mx-auto">
      <h1 className="text-xl font-bold mb-4">Standings</h1>
      <div className="space-y-8">
        {results.map((r) => {
          if (!r.data) return null
          const { conglomerate, tier1, tier2 } = r.data
          return (
            <section key={conglomerate.id}>
              <div className="flex items-center gap-3 mb-3">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: conglomerate.primary_color }}
                />
                <h2 className="text-base font-semibold">{conglomerate.full_name}</h2>
                <span className="text-text-muted text-sm">{conglomerate.network}</span>
              </div>
              {tier1.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-xs text-text-muted uppercase tracking-wider mb-1">Tier 1</h3>
                  <StandingsTable programs={tier1} />
                </div>
              )}
              {tier2.length > 0 && (
                <div>
                  <h3 className="text-xs text-text-muted uppercase tracking-wider mb-1">Tier 2</h3>
                  <StandingsTable programs={tier2} />
                </div>
              )}
            </section>
          )
        })}
      </div>
    </div>
  )
}
