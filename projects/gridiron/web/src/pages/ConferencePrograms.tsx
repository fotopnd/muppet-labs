import { useParams, Link } from 'react-router-dom'
import { useAllConglomerates, useConglomerateStandings } from '@/api/hooks'
import type { ProgramStanding } from '@/types'

function ProgramList({ programs, code }: { programs: ProgramStanding[]; code: string }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {programs.map(p => (
        <Link
          key={p.id}
          to={`/conference/${code}/programs/${p.id}`}
          className="flex items-center gap-3 bg-surface border border-border rounded-lg p-3 hover:border-accent/40 transition-colors"
        >
          <span className="text-2xl">{p.emoji}</span>
          <div>
            <div className="font-semibold text-sm">{p.name}</div>
            <div className="text-xs text-text-muted mt-0.5">
              {p.city} · {p.wins}–{p.losses} · ELO {Math.round(p.elo)}
            </div>
          </div>
        </Link>
      ))}
    </div>
  )
}

export default function ConferencePrograms() {
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
        <h2 className="text-xs font-semibold uppercase tracking-widest text-text-muted mb-3">
          Tier 1
        </h2>
        <ProgramList programs={standings.tier1} code={code!} />
      </section>
      <section>
        <h2 className="text-xs font-semibold uppercase tracking-widest text-text-muted mb-3">
          Tier 2
        </h2>
        <ProgramList programs={standings.tier2} code={code!} />
      </section>
    </div>
  )
}
