import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/api/client'
import { useGameStream } from '@/api/hooks'
import StatusBadge from '@/components/StatusBadge'
import type { GameBoxscore, GamecastState, GameDetail, GamePlay, PlayerBoxscore, SsePlayEvent } from '@/types'

const NO_YARDS_TYPES = new Set([
  'PASS_INCOMPLETE', 'PASS_DEFLECTION', 'PUNT', 'FIELD_GOAL_ATTEMPT',
  'PAT_CONVERSION', 'PAT_MISS', 'TWO_POINT_CONVERSION',
])

const SCORING_TYPES = new Set([
  'TOUCHDOWN', 'FIELD_GOAL_ATTEMPT', 'SAFETY', 'PAT_CONVERSION', 'TWO_POINT_CONVERSION',
])

function abbrevName(fullName: string): string {
  const spaceIdx = fullName.indexOf(' ')
  if (spaceIdx < 1) return fullName
  return `${fullName.charAt(0)}. ${fullName.slice(spaceIdx + 1)}`
}

function sseToPlay(e: SsePlayEvent): GamePlay {
  return {
    play_number: e.play_number,
    quarter: e.quarter,
    possession: e.possession,
    play_type: e.play_type,
    yards_gained: e.yards_gained,
    field_pos_before: e.field_pos_before,
    field_pos_after: e.field_pos_after,
    score_home: e.score_home,
    score_away: e.score_away,
    description: e.description,
    down: e.down,
    distance: e.distance,
  }
}

export default function Gamecast() {
  const { gameId: gameIdParam } = useParams<{ gameId: string }>()
  const gameId = parseInt(gameIdParam ?? '0', 10)
  const [state, setState] = useState<GamecastState>({ status: 'loading' })
  const [playsFilter, setPlaysFilter] = useState<'all' | 'scoring'>('all')
  const qc = useQueryClient()

  useEffect(() => {
    if (!gameId) return
    let cancelled = false
    void (async () => {
      try {
        const game = await apiFetch<GameDetail>(`/games/${gameId}`)
        if (cancelled) return
        qc.setQueryData(['game', gameId], game)

        if (game.status === 'scheduled') {
          setState({ status: 'scheduled', game })
        } else if (game.status === 'complete') {
          const [plays, boxscore] = await Promise.all([
            apiFetch<GamePlay[]>(`/games/${gameId}/plays`),
            apiFetch<GameBoxscore>(`/games/${gameId}/boxscore`),
          ])
          if (!cancelled) setState({ status: 'complete', game, plays, boxscore })
        } else {
          const [plays, boxscore] = await Promise.all([
            apiFetch<GamePlay[]>(`/games/${gameId}/plays`),
            apiFetch<GameBoxscore>(`/games/${gameId}/boxscore`),
          ])
          if (!cancelled) {
            const latest = plays[plays.length - 1]
            setState({
              status: 'live',
              game,
              plays: [...plays].reverse(),
              home_score: latest?.score_home ?? 0,
              away_score: latest?.score_away ?? 0,
              quarter: latest?.quarter ?? 1,
              down: latest?.down ?? null,
              distance: latest?.distance ?? null,
              field_pos: latest?.field_pos_after ?? null,
              possession: latest?.possession ?? null,
              boxscore,
            })
          }
        }
      } catch {
        if (!cancelled) setState({ status: 'scheduled', game: undefined as unknown as GameDetail })
      }
    })()
    return () => { cancelled = true }
  }, [gameId, qc])

  useGameStream(
    gameId,
    state.status === 'live',
    (e: SsePlayEvent) => {
      setState((prev) => {
        if (prev.status !== 'live') return prev
        // REST seed and SSE can overlap — skip adding plays we already have
        const latestPlayNum = prev.plays[0]?.play_number ?? 0
        const isNew = e.play_number > latestPlayNum
        return {
          ...prev,
          plays: isNew ? [sseToPlay(e), ...prev.plays] : prev.plays,
          home_score: e.score_home,
          away_score: e.score_away,
          quarter: e.quarter,
          down: e.down,
          distance: e.distance,
          field_pos: e.field_pos_after,
          possession: e.possession,
        }
      })
    },
    () => {
      void apiFetch<GameBoxscore>(`/games/${gameId}/boxscore`).then((boxscore) => {
        setState((prev) => {
          if (prev.status !== 'live') return prev
          return {
            status: 'complete',
            game: prev.game,
            plays: [...prev.plays].reverse(),
            boxscore,
          }
        })
      })
    },
  )

  if (state.status === 'loading') {
    return <div className="p-6 text-text-muted">Loading game...</div>
  }

  if (state.status === 'scheduled') {
    const { game } = state
    return (
      <div className="p-4 md:p-6 max-w-2xl mx-auto">
        <MatchupHeader
          homeEmoji={game.home.emoji} homeName={game.home.name}
          awayEmoji={game.away.emoji} awayName={game.away.name}
          homeScore={null} awayScore={null}
          status="scheduled" week={game.week} slot={game.broadcast_slot}
        />
        <p className="text-center text-text-muted mt-8">Game not yet started</p>
      </div>
    )
  }

  if (state.status === 'live') {
    const { game, plays, home_score, away_score, quarter, down, distance, field_pos, possession, boxscore } = state
    const filteredPlays = playsFilter === 'scoring'
      ? plays.filter(p => SCORING_TYPES.has(p.play_type))
      : plays

    return (
      <div className="p-4 md:p-6 max-w-5xl mx-auto">
        <MatchupHeader
          homeEmoji={game.home.emoji} homeName={game.home.name}
          awayEmoji={game.away.emoji} awayName={game.away.name}
          homeScore={home_score} awayScore={away_score}
          status="live" week={game.week} slot={game.broadcast_slot} quarter={quarter}
        />
        <DriveChart
          down={down} distance={distance} fieldPos={field_pos}
          possession={possession}
          homeAbbr={game.home.name.slice(0, 3).toUpperCase()}
          awayAbbr={game.away.name.slice(0, 3).toUpperCase()}
        />
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-4">
          <div>
            <PlaysToggle filter={playsFilter} onChange={setPlaysFilter} count={filteredPlays.length} />
            <div className="space-y-0">
              {filteredPlays.slice(0, 50).map((p) => (
                <PlayRow key={p.play_number} play={p} />
              ))}
            </div>
          </div>
          <div>
            <TeamLeadersWidget game={game} boxscore={boxscore} />
            <StatPanel game={game} boxscore={boxscore} />
          </div>
        </div>
      </div>
    )
  }

  // complete
  const { game, plays, boxscore } = state
  const filteredPlays = playsFilter === 'scoring'
    ? plays.filter(p => SCORING_TYPES.has(p.play_type))
    : plays

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto">
      <MatchupHeader
        homeEmoji={game.home.emoji} homeName={game.home.name}
        awayEmoji={game.away.emoji} awayName={game.away.name}
        homeScore={game.home_score} awayScore={game.away_score}
        status="complete" week={game.week} slot={game.broadcast_slot}
      />
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-4 mt-2">
        <div>
          <PlaysToggle filter={playsFilter} onChange={setPlaysFilter} count={filteredPlays.length} />
          <div className="mt-2 space-y-0 max-h-[600px] overflow-y-auto">
            {filteredPlays.map((p) => (
              <PlayRow key={p.play_number} play={p} />
            ))}
          </div>
        </div>
        <div>
          <TeamLeadersWidget game={game} boxscore={boxscore} />
          <StatPanel game={game} boxscore={boxscore} />
        </div>
      </div>
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────────────────────

function MatchupHeader({
  homeEmoji, homeName, awayEmoji, awayName,
  homeScore, awayScore, status, week, slot, quarter,
}: {
  homeEmoji: string; homeName: string
  awayEmoji: string; awayName: string
  homeScore: number | null; awayScore: number | null
  status: 'scheduled' | 'live' | 'complete'
  week: number; slot: string; quarter?: number
}) {
  return (
    <div className="bg-surface border border-border rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <StatusBadge status={status} />
        <span className="text-xs text-text-muted">
          Wk {week} · {slot.replace(/_/g, ' ')}
          {quarter ? ` · Q${quarter}` : ''}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 text-lg">
            <span>{homeEmoji}</span>
            <span className="font-semibold">{homeName}</span>
          </div>
          <div className="flex items-center gap-2 text-lg mt-1">
            <span>{awayEmoji}</span>
            <span className="font-semibold">{awayName}</span>
          </div>
        </div>
        {homeScore !== null && awayScore !== null && (
          <div className="text-right">
            <div className="text-3xl font-bold tabular-nums">{homeScore}</div>
            <div className="text-3xl font-bold tabular-nums">{awayScore}</div>
          </div>
        )}
      </div>
    </div>
  )
}

function DriveChart({
  down, distance, fieldPos, possession, homeAbbr, awayAbbr,
}: {
  down: number | null
  distance: number | null
  fieldPos: number | null
  possession: string | null
  homeAbbr: string
  awayAbbr: string
}) {
  if (down == null || distance == null || fieldPos == null || !possession) {
    return <div className="bg-surface border border-border rounded-lg p-3 mb-4 h-16" />
  }

  const teamLabel = possession === 'home' ? homeAbbr : awayAbbr
  const ordinals = ['', '1ST', '2ND', '3RD', '4TH']
  const downStr = ordinals[down] ?? `${down}TH`

  const yardLine = fieldPos <= 50 ? fieldPos : 100 - fieldPos
  const side = fieldPos < 50 ? 'OWN' : fieldPos === 50 ? 'MID' : 'OPP'
  const posLabel = side === 'MID' ? '50' : `${side} ${yardLine}`

  return (
    <div className="bg-surface border border-border rounded-lg p-3 mb-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-accent">{teamLabel} BALL</span>
        <span className="text-xs font-mono text-text-primary">
          {downStr} &amp; {distance} · {posLabel}
        </span>
      </div>
      <div className="relative h-4 bg-border/40 rounded overflow-hidden">
        <div className="absolute top-0 bottom-0 left-1/2 w-px bg-border/80" />
        {[10, 20, 30, 40, 60, 70, 80, 90].map((y) => (
          <div key={y} className="absolute top-0 bottom-0 w-px bg-border/40" style={{ left: `${y}%` }} />
        ))}
        <div
          className="absolute top-0.5 bottom-0.5 w-2 rounded-sm bg-accent transition-all duration-500"
          style={{ left: `calc(${fieldPos}% - 4px)` }}
        />
      </div>
      <div className="flex justify-between mt-1 text-[10px] text-text-muted">
        <span>HOME</span>
        <span>50</span>
        <span>AWAY</span>
      </div>
    </div>
  )
}

function PlaysToggle({ filter, onChange, count }: {
  filter: 'all' | 'scoring'
  onChange: (v: 'all' | 'scoring') => void
  count: number
}) {
  return (
    <div className="flex items-center gap-1 mb-3">
      {(['all', 'scoring'] as const).map((v) => (
        <button
          key={v}
          onClick={() => onChange(v)}
          className={`px-3 py-1 text-xs rounded-full border transition-colors ${
            filter === v
              ? 'bg-accent text-white border-accent'
              : 'border-border text-text-muted hover:text-text-primary'
          }`}
        >
          {v === 'all' ? 'All Plays' : 'Scoring Plays'}
        </button>
      ))}
      <span className="ml-2 text-xs text-text-muted">{count} plays</span>
    </div>
  )
}

function PlayRow({ play }: { play: GamePlay }) {
  const showYards = !NO_YARDS_TYPES.has(play.play_type) && play.yards_gained != null
  const yardsDisplay = showYards
    ? play.yards_gained! > 0 ? `+${play.yards_gained}y` : `${play.yards_gained}y`
    : ''

  return (
    <div className="flex items-start gap-2 text-xs py-1.5 border-b border-border/30">
      <span className="text-text-muted shrink-0 w-12">
        Q{play.quarter} #{play.play_number}
      </span>
      <span className="flex-1">{play.description}</span>
      {yardsDisplay && (
        <span className="text-text-muted shrink-0 tabular-nums">{yardsDisplay}</span>
      )}
    </div>
  )
}

function topBy(players: PlayerBoxscore[], key: 'pass_yards' | 'rush_yards' | 'receiving_yards'): PlayerBoxscore | undefined {
  return [...players].filter(p => p[key] > 0).sort((a, b) => b[key] - a[key])[0]
}

function TeamLeadersWidget({ game, boxscore }: { game: GameDetail; boxscore: GameBoxscore }) {
  const sides = [
    { team: game.home, players: boxscore.home },
    { team: game.away, players: boxscore.away },
  ]
  return (
    <div className="bg-surface border border-border rounded-lg p-3 mb-3">
      {sides.map(({ team, players }, i) => {
        const passer = topBy(players, 'pass_yards')
        const rusher = topBy(players, 'rush_yards')
        const receiver = topBy(players, 'receiving_yards')
        return (
          <div key={team.program_id} className={i > 0 ? 'mt-3 pt-3 border-t border-border/50' : ''}>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-base">{team.emoji}</span>
              <span className="text-xs font-semibold">{team.name}</span>
            </div>
            {passer && (
              <div className="flex justify-between text-[11px] mb-0.5">
                <span className="text-text-muted w-8">PASS</span>
                <span className="text-right">
                  {abbrevName(passer.name)} {passer.pass_completions}/{passer.pass_attempts} {passer.pass_yards}y
                  {passer.pass_tds > 0 ? ` ${passer.pass_tds}TD` : ''}
                </span>
              </div>
            )}
            {rusher && (
              <div className="flex justify-between text-[11px] mb-0.5">
                <span className="text-text-muted w-8">RUSH</span>
                <span className="text-right">
                  {abbrevName(rusher.name)} {rusher.rush_attempts}att {rusher.rush_yards}y
                  {rusher.rush_tds > 0 ? ` ${rusher.rush_tds}TD` : ''}
                </span>
              </div>
            )}
            {receiver && (
              <div className="flex justify-between text-[11px]">
                <span className="text-text-muted w-8">REC</span>
                <span className="text-right">
                  {abbrevName(receiver.name)} {receiver.receptions}/{receiver.targets} {receiver.receiving_yards}y
                  {receiver.receiving_tds > 0 ? ` ${receiver.receiving_tds}TD` : ''}
                </span>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function StatPanel({ game, boxscore }: { game: GameDetail; boxscore: GameBoxscore }) {
  const sides = [
    { team: game.home, players: boxscore.home },
    { team: game.away, players: boxscore.away },
  ]
  return (
    <div className="bg-surface border border-border rounded-lg p-3">
      {sides.map(({ team, players }, i) => {
        const passers = [...players].filter(p => p.pass_yards > 0 || p.pass_tds > 0).sort((a, b) => b.pass_yards - a.pass_yards)
        const rushers = [...players].filter(p => p.rush_yards > 0 || p.rush_tds > 0).sort((a, b) => b.rush_yards - a.rush_yards)
        const receivers = [...players].filter(p => p.receiving_yards > 0 || p.receiving_tds > 0).sort((a, b) => b.receiving_yards - a.receiving_yards)
        if (!passers.length && !rushers.length && !receivers.length) return null
        return (
          <div key={team.program_id} className={i > 0 ? 'mt-4 pt-4 border-t border-border/50' : ''}>
            <div className="flex items-center gap-1.5 mb-2">
              <span className="text-sm">{team.emoji}</span>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">{team.name}</span>
            </div>
            {passers.length > 0 && (
              <StatTable
                label="Passing"
                rows={passers.map(p => ({
                  id: p.player_id,
                  name: abbrevName(p.name),
                  cols: [`${p.pass_completions}/${p.pass_attempts}`, String(p.pass_yards), String(p.pass_tds)],
                }))}
                headers={['C/A', 'YDS', 'TD']}
              />
            )}
            {rushers.length > 0 && (
              <StatTable
                label="Rushing"
                rows={rushers.map(p => ({
                  id: p.player_id,
                  name: abbrevName(p.name),
                  cols: [String(p.rush_attempts), String(p.rush_yards), String(p.rush_tds)],
                }))}
                headers={['ATT', 'YDS', 'TD']}
              />
            )}
            {receivers.length > 0 && (
              <StatTable
                label="Receiving"
                rows={receivers.map(p => ({
                  id: p.player_id,
                  name: abbrevName(p.name),
                  cols: [`${p.receptions}/${p.targets}`, String(p.receiving_yards), String(p.receiving_tds)],
                }))}
                headers={['REC/TGT', 'YDS', 'TD']}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

function StatTable({ label, rows, headers }: {
  label: string
  rows: { id: number; name: string; cols: string[] }[]
  headers: string[]
}) {
  return (
    <div className="mb-3">
      <p className="text-[10px] text-text-muted uppercase tracking-wider mb-1">{label}</p>
      <table className="w-full text-[11px]">
        <thead>
          <tr className="text-text-muted text-[10px]">
            <th className="text-left pb-0.5 font-normal">Name</th>
            {headers.map(h => (
              <th key={h} className="text-right pb-0.5 font-normal">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map(row => (
            <tr key={row.id} className="border-t border-border/30">
              <td className="py-0.5 pr-2">{row.name}</td>
              {row.cols.map((c, j) => (
                <td key={j} className="text-right py-0.5 tabular-nums">{c}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
