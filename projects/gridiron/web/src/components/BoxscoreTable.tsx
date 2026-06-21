import type { PlayerBoxscore } from '@/types'

type Props = { players: PlayerBoxscore[]; label: string }

const QB_POS = new Set(['QB'])
const RB_POS = new Set(['RB', 'FB'])
const RECV_POS = new Set(['WR', 'TE'])
const DEF_POS = new Set(['DL', 'LB', 'DB', 'DE', 'DT', 'CB', 'S', 'FS', 'SS'])

function hasStats(p: PlayerBoxscore, group: 'pass' | 'rush' | 'recv' | 'def') {
  if (group === 'pass') return p.pass_yards > 0 || p.pass_tds > 0
  if (group === 'rush') return p.rush_yards > 0 || p.rush_tds > 0
  if (group === 'recv') return p.receiving_yards > 0 || p.receiving_tds > 0
  return p.sacks > 0 || p.ints_def > 0
}

export default function BoxscoreTable({ players, label }: Props) {
  const passers = players.filter((p) => QB_POS.has(p.position) && hasStats(p, 'pass'))
  const rushers = players.filter((p) => RB_POS.has(p.position) && hasStats(p, 'rush'))
  const receivers = players.filter((p) => RECV_POS.has(p.position) && hasStats(p, 'recv'))
  const defenders = players.filter((p) => DEF_POS.has(p.position) && hasStats(p, 'def'))

  if (!passers.length && !rushers.length && !receivers.length && !defenders.length) {
    return null
  }

  return (
    <div className="mb-4">
      <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-2">
        {label}
      </h3>

      {passers.length > 0 && (
        <table className="w-full text-sm mb-3">
          <thead>
            <tr className="text-text-muted text-xs">
              <th className="text-left py-1 pr-3">Name</th>
              <th className="text-right py-1 px-2">C/A</th>
              <th className="text-right py-1 px-2">Yds</th>
              <th className="text-right py-1 pl-2">TD</th>
            </tr>
          </thead>
          <tbody>
            {passers.map((p) => (
              <tr key={p.player_id} className="border-t border-border/50">
                <td className="py-1 pr-3">{p.name}</td>
                <td className="text-right py-1 px-2 text-text-muted">
                  {p.pass_completions}/{p.pass_attempts}
                </td>
                <td className="text-right py-1 px-2">{p.pass_yards}</td>
                <td className="text-right py-1 pl-2">{p.pass_tds}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {rushers.length > 0 && (
        <table className="w-full text-sm mb-3">
          <thead>
            <tr className="text-text-muted text-xs">
              <th className="text-left py-1 pr-3">Name</th>
              <th className="text-right py-1 px-2">Att</th>
              <th className="text-right py-1 px-2">Yds</th>
              <th className="text-right py-1 pl-2">TD</th>
            </tr>
          </thead>
          <tbody>
            {rushers.map((p) => (
              <tr key={p.player_id} className="border-t border-border/50">
                <td className="py-1 pr-3">{p.name}</td>
                <td className="text-right py-1 px-2 text-text-muted">{p.rush_attempts}</td>
                <td className="text-right py-1 px-2">{p.rush_yards}</td>
                <td className="text-right py-1 pl-2">{p.rush_tds}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {receivers.length > 0 && (
        <table className="w-full text-sm mb-3">
          <thead>
            <tr className="text-text-muted text-xs">
              <th className="text-left py-1 pr-3">Name</th>
              <th className="text-right py-1 px-2">Rec/Tgt</th>
              <th className="text-right py-1 px-2">Yds</th>
              <th className="text-right py-1 pl-2">TD</th>
            </tr>
          </thead>
          <tbody>
            {receivers.map((p) => (
              <tr key={p.player_id} className="border-t border-border/50">
                <td className="py-1 pr-3">{p.name}</td>
                <td className="text-right py-1 px-2 text-text-muted">
                  {p.receptions}/{p.targets}
                </td>
                <td className="text-right py-1 px-2">{p.receiving_yards}</td>
                <td className="text-right py-1 pl-2">{p.receiving_tds}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {defenders.length > 0 && (
        <table className="w-full text-sm mb-3">
          <thead>
            <tr className="text-text-muted text-xs">
              <th className="text-left py-1 pr-3">Name</th>
              <th className="text-right py-1 px-2">Sacks</th>
              <th className="text-right py-1 pl-2">INT</th>
            </tr>
          </thead>
          <tbody>
            {defenders.map((p) => (
              <tr key={p.player_id} className="border-t border-border/50">
                <td className="py-1 pr-3">{p.name}</td>
                <td className="text-right py-1 px-2">{p.sacks}</td>
                <td className="text-right py-1 pl-2">{p.ints_def}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
