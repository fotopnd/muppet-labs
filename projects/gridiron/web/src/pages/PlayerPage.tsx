import { useParams, Link } from 'react-router-dom'
import { usePlayer } from '@/api/hooks'
import type { PlayerDetail } from '@/types'

const YEAR_CLASS = ['', 'Freshman', 'Sophomore', 'Junior', 'Senior'] as const

function pct(num: number, den: number) {
  return den > 0 ? ((num / den) * 100).toFixed(1) : '—'
}
function avg(num: number, den: number) {
  return den > 0 ? (num / den).toFixed(1) : '—'
}
function passerRating(comp: number, att: number, yds: number, td: number, int_: number) {
  if (att === 0) return '—'
  const clamp = (x: number) => Math.max(0, Math.min(2.375, x))
  const a = clamp((comp / att - 0.3) / 0.2)
  const b = clamp((yds / att - 3) / 4)
  const c = clamp((td / att) / 0.05)
  const d = clamp(0.095 - (int_ / att) / 4)
  return ((a + b + c + d) / 6 * 100).toFixed(1)
}

function StatTable({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-[10px] font-semibold uppercase tracking-widest text-text-muted mb-2">{label}</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">{children}</table>
      </div>
    </div>
  )
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="text-right text-[10px] text-text-muted font-medium py-1.5 px-2 whitespace-nowrap first:text-left">{children}</th>
}
function Td({ children }: { children: React.ReactNode }) {
  return <td className="text-right tabular-nums py-1.5 px-2 first:text-left">{children}</td>
}

function PassingTable({ p }: { p: PlayerDetail }) {
  if (p.pass_attempts === 0) return null
  const rating = passerRating(p.pass_completions, p.pass_attempts, p.pass_yards, p.pass_tds, p.interceptions)
  return (
    <StatTable label="Passing">
      <thead>
        <tr className="border-b border-border">
          <Th>GP</Th><Th>COMP</Th><Th>ATT</Th><Th>PCT</Th>
          <Th>YDS</Th><Th>YPA</Th><Th>TD</Th><Th>INT</Th><Th>RTG</Th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <Td>{p.games_played}</Td>
          <Td>{p.pass_completions}</Td>
          <Td>{p.pass_attempts}</Td>
          <Td>{pct(p.pass_completions, p.pass_attempts)}</Td>
          <Td>{p.pass_yards}</Td>
          <Td>{avg(p.pass_yards, p.pass_attempts)}</Td>
          <Td>{p.pass_tds}</Td>
          <Td>{p.interceptions}</Td>
          <Td>{rating}</Td>
        </tr>
      </tbody>
    </StatTable>
  )
}

function RushingTable({ p }: { p: PlayerDetail }) {
  if (p.rush_attempts === 0) return null
  return (
    <StatTable label="Rushing">
      <thead>
        <tr className="border-b border-border">
          <Th>GP</Th><Th>ATT</Th><Th>YDS</Th><Th>AVG</Th><Th>TD</Th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <Td>{p.games_played}</Td>
          <Td>{p.rush_attempts}</Td>
          <Td>{p.rush_yards}</Td>
          <Td>{avg(p.rush_yards, p.rush_attempts)}</Td>
          <Td>{p.rush_tds}</Td>
        </tr>
      </tbody>
    </StatTable>
  )
}

function ReceivingTable({ p }: { p: PlayerDetail }) {
  if (p.targets === 0 && p.receptions === 0) return null
  return (
    <StatTable label="Receiving">
      <thead>
        <tr className="border-b border-border">
          <Th>GP</Th><Th>REC</Th><Th>TGT</Th><Th>YDS</Th><Th>AVG</Th><Th>TD</Th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <Td>{p.games_played}</Td>
          <Td>{p.receptions}</Td>
          <Td>{p.targets}</Td>
          <Td>{p.receiving_yards}</Td>
          <Td>{avg(p.receiving_yards, p.receptions)}</Td>
          <Td>{p.receiving_tds}</Td>
        </tr>
      </tbody>
    </StatTable>
  )
}

function DefenseTable({ p }: { p: PlayerDetail }) {
  if (p.tackles === 0 && p.sacks === 0 && p.ints_def === 0 && p.forced_fumbles === 0) return null
  return (
    <StatTable label="Defense">
      <thead>
        <tr className="border-b border-border">
          <Th>GP</Th><Th>TACKLES</Th><Th>SACKS</Th><Th>INT</Th><Th>FF</Th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <Td>{p.games_played}</Td>
          <Td>{p.tackles}</Td>
          <Td>{p.sacks}</Td>
          <Td>{p.ints_def}</Td>
          <Td>{p.forced_fumbles}</Td>
        </tr>
      </tbody>
    </StatTable>
  )
}

function KickingTable({ p }: { p: PlayerDetail }) {
  if (p.fg_attempts === 0) return null
  return (
    <StatTable label="Kicking">
      <thead>
        <tr className="border-b border-border">
          <Th>GP</Th><Th>FGM</Th><Th>FGA</Th><Th>PCT</Th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <Td>{p.games_played}</Td>
          <Td>{p.fg_made}</Td>
          <Td>{p.fg_attempts}</Td>
          <Td>{pct(p.fg_made, p.fg_attempts)}</Td>
        </tr>
      </tbody>
    </StatTable>
  )
}

function SeasonStats({ p }: { p: PlayerDetail }) {
  const tables = [
    <PassingTable key="pass" p={p} />,
    <RushingTable key="rush" p={p} />,
    <ReceivingTable key="rec" p={p} />,
    <DefenseTable key="def" p={p} />,
    <KickingTable key="kick" p={p} />,
  ].filter(el => el !== null)

  if (tables.length === 0 || p.games_played === 0) return null

  return (
    <div className="bg-surface border border-border rounded-lg p-4 space-y-5">
      <h2 className="text-xs font-semibold uppercase tracking-widest text-text-muted">
        Season Stats <span className="font-normal normal-case">({p.games_played} GP)</span>
      </h2>
      {tables}
    </div>
  )
}

export default function PlayerPage() {
  const { playerId: idParam } = useParams<{ playerId: string }>()
  const playerId = parseInt(idParam ?? '0', 10)
  const { data: p, isLoading, isError } = usePlayer(playerId)

  if (isLoading) return <div className="p-6 text-text-muted">Loading...</div>
  if (isError || !p) return <div className="p-6 text-text-muted">Player not found.</div>

  const yearLabel = YEAR_CLASS[p.year] ?? `Year ${p.year}`

  return (
    <div className="p-4 md:p-6 max-w-2xl mx-auto space-y-4">
      {/* Header */}
      <div className="bg-surface border border-border rounded-lg p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-text-muted text-xs font-semibold uppercase tracking-widest mb-1">
              #{p.jersey_num} · {p.position}
            </div>
            <h1 className="text-2xl font-bold">{p.first_name} {p.last_name}</h1>
            <Link
              to={`/conference/${p.conglomerate_code}/programs/${p.program_id}`}
              className="text-sm text-text-muted hover:text-accent transition-colors mt-0.5 inline-block"
            >
              {p.program_emoji} {p.program_name}
            </Link>
          </div>
          <span className="text-4xl select-none">{p.program_emoji}</span>
        </div>
      </div>

      {/* Bio */}
      <div className="bg-surface border border-border rounded-lg p-4">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-text-muted mb-3">Bio</h2>
        <dl className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-3 text-sm">
          <div>
            <dt className="text-[10px] text-text-muted uppercase tracking-wider mb-0.5">Class</dt>
            <dd className="font-medium">{yearLabel}</dd>
          </div>
          <div>
            <dt className="text-[10px] text-text-muted uppercase tracking-wider mb-0.5">Position</dt>
            <dd className="font-medium">{p.position}</dd>
          </div>
          <div>
            <dt className="text-[10px] text-text-muted uppercase tracking-wider mb-0.5">Jersey</dt>
            <dd className="font-medium">#{p.jersey_num}</dd>
          </div>
          <div>
            <dt className="text-[10px] text-text-muted uppercase tracking-wider mb-0.5">Height</dt>
            <dd className="font-medium">{p.height_ft}'{p.height_in}"</dd>
          </div>
          <div>
            <dt className="text-[10px] text-text-muted uppercase tracking-wider mb-0.5">Weight</dt>
            <dd className="font-medium">{p.weight_lbs} lbs</dd>
          </div>
          <div>
            <dt className="text-[10px] text-text-muted uppercase tracking-wider mb-0.5">Hometown</dt>
            <dd className="font-medium">{p.hometown}, {p.state}</dd>
          </div>
        </dl>
      </div>

      {/* Season stats */}
      <SeasonStats p={p} />
    </div>
  )
}
