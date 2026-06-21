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

const PLAY_LABELS: Record<string, string> = {
  RUSH: 'Rush', PASS_COMPLETE: 'Pass', PASS_INCOMPLETE: 'Inc.',
  PASS_DEFLECTION: 'Def.', SACK: 'Sack', TACKLE_FOR_LOSS: 'TFL',
  TURNOVER_FUMBLE: 'Fumble', TURNOVER_INTERCEPTION: 'INT',
  PUNT: 'Punt', FIELD_GOAL_ATTEMPT: 'FG', TOUCHDOWN: 'TD', SAFETY: 'Safety',
}

const DRIVE_SKIP = new Set(['PAT_CONVERSION', 'PAT_MISS', 'TWO_POINT_CONVERSION'])

function getCurrentDrive(plays: GamePlay[], possession: string | null, quarter: number): GamePlay[] {
  if (!plays.length || !possession) return []
  const drive: GamePlay[] = []
  for (const play of plays) {
    if (DRIVE_SKIP.has(play.play_type)) continue
    if (play.possession !== possession) break
    if (quarter >= 3 && play.quarter <= 2) break
    drive.push(play)
  }
  return drive.reverse()
}

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
  const [fetchKey, setFetchKey] = useState(0)
  const qc = useQueryClient()

  async function handleReplay() {
    await apiFetch('/admin/replay', { method: 'POST' })
    setState({ status: 'loading' })
    setFetchKey(k => k + 1)
  }

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
  }, [gameId, qc, fetchKey])

  useGameStream(
    gameId,
    state.status === 'live',
    (e: SsePlayEvent) => {
      setState((prev) => {
        if (prev.status !== 'live') return prev
        // REST seed and SSE can overlap — skip adding plays we already have
        const latestPlayNum = prev.plays[0]?.play_number ?? 0
        const isNew = e.play_number > latestPlayNum
        const updated = {
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
        // Refetch boxscore every 5 new plays or on scoring events
        const SCORING_SSE = new Set(['TOUCHDOWN', 'FIELD_GOAL_ATTEMPT'])
        const shouldRefetch = isNew && (
          updated.plays.length % 5 === 0 || SCORING_SSE.has(e.play_type)
        )
        if (shouldRefetch) {
          void apiFetch<GameBoxscore>(`/games/${gameId}/boxscore`).then((boxscore) => {
            setState((s) => s.status === 'live' ? { ...s, boxscore } : s)
          })
        }
        return updated
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
    if (!game) return <div className="p-6 text-text-muted">Game not found.</div>
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
        {gameId === 153 && <ReplayButton onReplay={handleReplay} />}
        <DrivePanel
          down={down} distance={distance} fieldPos={field_pos}
          possession={possession} quarter={quarter} plays={plays}
          homeEmoji={game.home.emoji} awayEmoji={game.away.emoji}
          homeAbbr={game.home.name.slice(0, 3).toUpperCase()}
          awayAbbr={game.away.name.slice(0, 3).toUpperCase()}
          homeProgramId={game.home.program_id}
          awayProgramId={game.away.program_id}
        />
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-4">
          <div>
            <PlaysToggle filter={playsFilter} onChange={setPlaysFilter} count={filteredPlays.length} />
            <div className="space-y-0">
              {filteredPlays.slice(0, 50).map((p) => (
                <PlayRow key={`${p.play_number}_${p.play_type}`} play={p} />
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
      {gameId === 153 && <ReplayButton onReplay={handleReplay} />}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-4 mt-2">
        <div>
          <PlaysToggle filter={playsFilter} onChange={setPlaysFilter} count={filteredPlays.length} />
          <div className="mt-2 space-y-0 max-h-[600px] overflow-y-auto">
            {filteredPlays.map((p) => (
              <PlayRow key={`${p.play_number}_${p.play_type}`} play={p} />
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

function ReplayButton({ onReplay }: { onReplay: () => Promise<void> }) {
  const [loading, setLoading] = useState(false)
  return (
    <button
      onClick={async () => { setLoading(true); await onReplay(); setLoading(false) }}
      disabled={loading}
      className="mb-4 px-3 py-1.5 text-xs border border-border rounded hover:bg-surface/80 text-text-muted disabled:opacity-50 transition-colors"
    >
      {loading ? 'Restarting…' : '↺ Restart stream'}
    </button>
  )
}

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

const ROW = 2.5
const MIN_ROWS = 8

// Maps field_pos 0–100 to SVG x 10–90 (10-unit end zones each side)
function fx(pos: number): number { return 10 + pos * 0.8 }

function schoolColor(id: number): string {
  const hue = (id * 137) % 360
  return `hsl(${hue}, 72%, 38%)`
}

function schoolSecondary(id: number): string {
  const hue = (id * 137 + 150) % 360
  return `hsl(${hue}, 72%, 38%)`
}

function hslParts(c: string): [number, number, number] | null {
  const m = c.match(/hsl\(([\d.]+),\s*([\d.]+)%,\s*([\d.]+)%\)/)
  return m ? [parseFloat(m[1]!), parseFloat(m[2]!), parseFloat(m[3]!)] : null
}

// Near-white: very light or very desaturated
function isNearWhite(c: string): boolean {
  const p = hslParts(c)
  return p ? p[2] > 80 || p[1] < 15 : false
}

// Too similar to field green (#2d6a4f ≈ hsl 150, 40%, 30%)
function isNearFieldGreen(c: string): boolean {
  const p = hslParts(c)
  if (!p) return false
  return p[0] >= 100 && p[0] <= 175 && p[1] > 35 && p[2] > 15 && p[2] < 60
}

// End zone: primary color, lightened if it would blend into the field
function ezColor(id: number): string {
  const primary = schoolColor(id)
  if (isNearFieldGreen(primary)) {
    const [h, s] = hslParts(primary)!
    return `hsl(${h}, ${s}%, 65%)`  // much lighter — clearly distinct from field
  }
  return primary
}

// Arrow: white; fall back to secondary if primary is white; amber if secondary is also field-like
function arrowColor(id: number): string {
  if (isNearWhite(schoolColor(id))) {
    const sec = schoolSecondary(id)
    return isNearFieldGreen(sec) ? '#d97706' : sec
  }
  return '#ffffff'
}

function DrivePanel({
  down, distance, fieldPos, possession, quarter, plays,
  homeEmoji, awayEmoji, homeAbbr, awayAbbr, homeProgramId, awayProgramId,
}: {
  down: number | null; distance: number | null; fieldPos: number | null
  possession: string | null; quarter: number
  plays: GamePlay[]
  homeEmoji: string; awayEmoji: string; homeAbbr: string; awayAbbr: string
  homeProgramId: number; awayProgramId: number
}) {
  const drivePlays = getCurrentDrive(plays, possession, quarter)
  const teamLabel = possession === 'home' ? homeAbbr : awayAbbr
  const ordinals = ['', '1st', '2nd', '3rd', '4th']
  const downStr = down != null ? `${ordinals[down] ?? `${down}th`} & ${distance}` : null
  const yardLine = fieldPos != null ? (fieldPos <= 50 ? fieldPos : 100 - fieldPos) : null
  const side = fieldPos != null ? (fieldPos < 50 ? 'OWN' : fieldPos === 50 ? 'MID' : 'OPP') : null
  const posLabel = side === 'MID' ? '50' : (yardLine != null && side ? `${side} ${yardLine}` : '')

  const homeEzColor    = ezColor(homeProgramId)
  const awayEzColor    = ezColor(awayProgramId)
  const homeArrowColor = arrowColor(homeProgramId)
  const awayArrowColor = arrowColor(awayProgramId)

  const rowCount = Math.max(MIN_ROWS, drivePlays.length)
  const H = rowCount * ROW

  return (
    <div className="bg-surface border border-border rounded-lg p-3 mb-4">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[11px] font-semibold text-accent">{teamLabel} BALL</span>
        {downStr && (
          <span className="text-[11px] font-mono text-text-primary">
            {downStr}{posLabel ? ` · ${posLabel}` : ''}
          </span>
        )}
      </div>
      <svg viewBox={`0 0 100 ${H}`} style={{ width: '100%', display: 'block' }}>
        {/* End zones in school colors (field-similar hues are lightened for visibility) */}
        <rect x="0"  y="0" width="10" height={H} fill={homeEzColor} />
        <rect x="90" y="0" width="10" height={H} fill={awayEzColor} />
        {/* Playing field */}
        <rect x="10" y="0" width="80" height={H} fill="#2d6a4f" />
        {/* End zone emojis */}
        <text x="5"  y={H / 2} fontSize="2.5" textAnchor="middle" dominantBaseline="middle">{homeEmoji}</text>
        <text x="95" y={H / 2} fontSize="2.5" textAnchor="middle" dominantBaseline="middle">{awayEmoji}</text>
        {/* Goal lines */}
        <line x1={fx(0)}   y1="0" x2={fx(0)}   y2={H} stroke="white" strokeOpacity="0.6" strokeWidth="0.5" />
        <line x1={fx(100)} y1="0" x2={fx(100)} y2={H} stroke="white" strokeOpacity="0.6" strokeWidth="0.5" />
        {/* Major yard lines every 10 yards */}
        {[10, 20, 30, 40, 60, 70, 80, 90].map((yd) => (
          <line key={yd} x1={fx(yd)} y1="0" x2={fx(yd)} y2={H}
            stroke="white" strokeOpacity="0.3" strokeWidth="0.3" />
        ))}
        {/* 50-yard line — thicker */}
        <line x1={fx(50)} y1="0" x2={fx(50)} y2={H}
          stroke="white" strokeOpacity="0.7" strokeWidth="0.7" />
        {/* Hash marks at every 5-yard gap — short ticks at top and bottom */}
        {[5, 15, 25, 35, 45, 55, 65, 75, 85, 95].map((yd) => (
          <g key={yd}>
            <line x1={fx(yd)} y1="0"     x2={fx(yd)} y2="0.9"
              stroke="white" strokeOpacity="0.35" strokeWidth="0.25" />
            <line x1={fx(yd)} y1={H}     x2={fx(yd)} y2={H - 0.9}
              stroke="white" strokeOpacity="0.35" strokeWidth="0.25" />
          </g>
        ))}
        {/* Yard numbers — top and bottom */}
        {([10,20,30,40,50,60,70,80,90] as const).map((yd, i) => {
          const label = [10,20,30,40,50,40,30,20,10][i]
          return (
            <g key={yd}>
              <text x={fx(yd)} y="1.5" fontSize="1.6"
                fill="white" fillOpacity="0.55" textAnchor="middle">{label}</text>
              <text x={fx(yd)} y={H - 0.4} fontSize="1.6"
                fill="white" fillOpacity="0.55" textAnchor="middle" dominantBaseline="text-before-edge">{label}</text>
            </g>
          )
        })}
        {/* Play arrows */}
        {drivePlays.map((play, i) => {
          const cy = (i + 0.5) * ROW
          const startPos = play.field_pos_before ?? fieldPos ?? 50
          const endPos   = play.field_pos_after  ?? startPos
          const x1 = fx(startPos)
          const x2 = fx(endPos)
          const color = play.possession === 'home' ? homeArrowColor : awayArrowColor
          const right = x2 >= x1
          const AS = 0.8
          const x2shaft = right ? Math.max(x1, x2 - AS) : Math.min(x1, x2 + AS)
          const pts = right
            ? `${x2},${cy} ${x2 - AS},${cy - AS * 0.8} ${x2 - AS},${cy + AS * 0.8}`
            : `${x2},${cy} ${x2 + AS},${cy - AS * 0.8} ${x2 + AS},${cy + AS * 0.8}`
          const span = Math.abs(x2 - x1)

          return (
            <g key={`${play.play_number}_${play.play_type}`}>
              {span > 0.5 && (
                <line x1={x1} y1={cy} x2={x2shaft} y2={cy}
                  stroke={color} strokeWidth="1" strokeOpacity="1" strokeLinecap="round" />
              )}
              <polygon points={pts} fill={color} fillOpacity="1" />
            </g>
          )
        })}
        {/* Line of scrimmage */}
        {fieldPos != null && (
          <line x1={fx(fieldPos)} y1="0" x2={fx(fieldPos)} y2={H}
            stroke="#facc15" strokeOpacity="0.6" strokeWidth="0.5" strokeDasharray="1.5,1" />
        )}
      </svg>
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
