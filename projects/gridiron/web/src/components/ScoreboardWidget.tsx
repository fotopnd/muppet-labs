import { Link } from 'react-router-dom'
import type { ScheduleGame, SsePlayEvent } from '@/types'

function fx(pos: number): number { return 10 + pos * 0.8 }

function schoolColor(id: number): string {
  const hue = (id * 137) % 360
  return `hsl(${hue}, 72%, 38%)`
}

function hslParts(c: string): [number, number, number] | null {
  const m = c.match(/hsl\(([\d.]+),\s*([\d.]+)%,\s*([\d.]+)%\)/)
  return m ? [parseFloat(m[1]!), parseFloat(m[2]!), parseFloat(m[3]!)] : null
}

function isNearFieldGreen(c: string): boolean {
  const p = hslParts(c)
  return p ? p[0] >= 100 && p[0] <= 175 && p[1] > 35 && p[2] > 15 && p[2] < 60 : false
}

function ezColor(id: number): string {
  const primary = schoolColor(id)
  if (isNearFieldGreen(primary)) {
    const [h, s] = hslParts(primary)!
    return `hsl(${h}, ${s}%, 65%)`
  }
  return primary
}

const PLAYS_PER_QUARTER = 34
const SECS_PER_PLAY = 4.44

function derivedClock(play_number: number, quarter: number): string {
  const playsIntoQ = (play_number - 1) - (quarter - 1) * PLAYS_PER_QUARTER
  const secsLeft = Math.max(0, (PLAYS_PER_QUARTER - playsIntoQ) * SECS_PER_PLAY)
  const mins = Math.floor(secsLeft / 60)
  const secs = String(Math.floor(secsLeft % 60)).padStart(2, '0')
  return `Q${quarter} ${mins}:${secs}`
}

const ORDINALS = ['', '1st', '2nd', '3rd', '4th']

function formatSlot(slot: string): string {
  return slot.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function FieldStrip({
  homeProgramId, awayProgramId, ballPos, possession,
}: {
  homeProgramId: number
  awayProgramId: number
  ballPos: number | null
  possession?: string | undefined
}) {
  const homeEz = ezColor(homeProgramId)
  const awayEz = ezColor(awayProgramId)
  const ballX = ballPos != null ? fx(ballPos) : null
  const goingRight = possession === 'home'

  return (
    <svg viewBox="0 0 100 14" style={{ width: '100%', height: '16px', display: 'block' }}>
      {/* End zones */}
      <rect x="0"  y="0" width="10" height="10" fill={homeEz} />
      <rect x="90" y="0" width="10" height="10" fill={awayEz} />
      {/* Field */}
      <rect x="10" y="0" width="80" height="10" fill="#2d6a4f" />
      {/* Hash marks */}
      <line x1={fx(0)}  y1="0" x2={fx(0)}  y2="10" stroke="white" strokeOpacity="0.5" strokeWidth="0.5" />
      <line x1={fx(50)} y1="0" x2={fx(50)} y2="10" stroke="white" strokeOpacity="0.4" strokeWidth="0.4" />
      <line x1={fx(100)} y1="0" x2={fx(100)} y2="10" stroke="white" strokeOpacity="0.5" strokeWidth="0.5" />
      {/* HOME / AWAY labels inside end zones */}
      <text x="5" y="6.5" fontSize="3" textAnchor="middle" fill="white" fillOpacity="0.65">HOME</text>
      <text x="95" y="6.5" fontSize="3" textAnchor="middle" fill="white" fillOpacity="0.65">AWAY</text>
      {/* Ball */}
      {ballX != null && (
        <>
          <circle cx={ballX} cy="5" r="1.5" fill="white" />
          {goingRight
            ? <polygon points={`${ballX + 2.5},5 ${ballX + 0.5},3.5 ${ballX + 0.5},6.5`} fill="white" fillOpacity="0.7" />
            : <polygon points={`${ballX - 2.5},5 ${ballX - 0.5},3.5 ${ballX - 0.5},6.5`} fill="white" fillOpacity="0.7" />
          }
        </>
      )}
    </svg>
  )
}

export default function ScoreboardWidget({
  game, liveState,
}: {
  game: ScheduleGame
  liveState?: SsePlayEvent | undefined
}) {
  const isLive = game.status === 'live' && !!liveState
  const isComplete = game.status === 'complete'

  const homeScore = isLive ? liveState!.score_home : (isComplete ? game.home_score : null)
  const awayScore = isLive ? liveState!.score_away : (isComplete ? game.away_score : null)
  const scoreStr = (s: number | null) => s == null ? '—' : String(s)

  const statusLabel = isLive ? '● LIVE' : isComplete ? 'FINAL' : formatSlot(game.broadcast_slot)
  const statusCls = isLive ? 'text-accent font-semibold' : 'text-text-muted'

  const infoLine = (() => {
    if (!isLive || !liveState) return null
    const clock = derivedClock(liveState.play_number, liveState.quarter)
    const possName = liveState.possession === 'home'
      ? game.home_name.split(' ')[0]
      : game.away_name.split(' ')[0]
    const downDist = liveState.down != null && liveState.distance != null
      ? `${ORDINALS[liveState.down] ?? `${liveState.down}th`} & ${liveState.distance}`
      : null
    return [possName ? `${possName} BALL` : null, downDist, clock].filter(Boolean).join(' · ')
  })()

  const ballPos = liveState?.field_pos_after ?? null

  return (
    <Link
      to={`/games/${game.game_id}`}
      className="block bg-surface border border-border rounded-lg overflow-hidden hover:border-accent/40 transition-colors"
    >
      {/* Header row */}
      <div className="px-3 pt-2 pb-1 flex items-center justify-between gap-2">
        <span className={`text-[10px] ${statusCls}`}>{statusLabel}</span>
        <span className="text-[10px] text-text-muted">Wk {game.week}</span>
      </div>

      {/* Team rows */}
      <div className="px-3 pb-1 space-y-0.5">
        <div className="flex items-center gap-2 text-sm">
          <span>{game.home_emoji}</span>
          <span className="flex-1 truncate">{game.home_name}</span>
          <span className="tabular-nums font-bold shrink-0">{scoreStr(homeScore)}</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span>{game.away_emoji}</span>
          <span className="flex-1 truncate">{game.away_name}</span>
          <span className="tabular-nums font-bold shrink-0">{scoreStr(awayScore)}</span>
        </div>
      </div>

      {/* Info line (live only) */}
      {infoLine && (
        <div className="px-3 pb-1 text-[10px] text-text-muted truncate">{infoLine}</div>
      )}

      {/* Field strip */}
      <FieldStrip
        homeProgramId={game.home_program_id}
        awayProgramId={game.away_program_id}
        ballPos={ballPos}
        possession={liveState?.possession}
      />
    </Link>
  )
}
