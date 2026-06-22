import { Link } from 'react-router-dom'
import type { ScheduleGame, SsePlayEvent } from '@/types'

// Copied from Gamecast.tsx — maps field_pos 0–100 to SVG x 10–90
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

function FieldStrip({
  homeProgramId, awayProgramId, liveState,
}: {
  homeProgramId: number
  awayProgramId: number
  liveState?: SsePlayEvent | undefined
}) {
  const homeEz = ezColor(homeProgramId)
  const awayEz = ezColor(awayProgramId)
  const ballX = liveState ? fx(liveState.field_pos_after ?? 50) : null
  const goingRight = liveState?.possession === 'home'
  const AS = 1.2

  return (
    <svg viewBox="0 0 100 10" style={{ width: '100%', height: '12px', display: 'block' }}>
      <rect x="0"  y="0" width="10"  height="10" fill={homeEz} />
      <rect x="90" y="0" width="10"  height="10" fill={awayEz} />
      <rect x="10" y="0" width="80"  height="10" fill="#2d6a4f" />
      <line x1={fx(0)}   y1="0" x2={fx(0)}   y2="10" stroke="white" strokeOpacity="0.5" strokeWidth="0.5" />
      <line x1={fx(50)}  y1="0" x2={fx(50)}  y2="10" stroke="white" strokeOpacity="0.4" strokeWidth="0.4" />
      <line x1={fx(100)} y1="0" x2={fx(100)} y2="10" stroke="white" strokeOpacity="0.5" strokeWidth="0.5" />
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
  const href = `/games/${game.game_id}`
  const homeScore = liveState ? liveState.score_home : game.home_score
  const awayScore = liveState ? liveState.score_away : game.away_score

  const statusLine = (() => {
    if (game.status === 'live' && liveState) {
      const clock = derivedClock(liveState.play_number, liveState.quarter)
      const downDist = liveState.down != null && liveState.distance != null
        ? `${ORDINALS[liveState.down] ?? `${liveState.down}th`} & ${liveState.distance}`
        : null
      const desc = liveState.description.length > 38
        ? `${liveState.description.slice(0, 38)}…`
        : liveState.description
      return [clock, downDist, desc].filter(Boolean).join(' · ')
    }
    if (game.status === 'complete') return 'FINAL'
    return game.broadcast_slot.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  })()

  return (
    <Link
      to={href}
      className="block bg-surface border border-border rounded-lg overflow-hidden hover:border-accent/40 transition-colors"
    >
      <FieldStrip
        homeProgramId={game.home_program_id}
        awayProgramId={game.away_program_id}
        liveState={liveState}
      />
      <div className="px-3 py-2">
        <div className="flex items-center justify-between gap-2 text-sm">
          <span className="truncate">
            <span className="mr-1">{game.home_emoji}</span>
            <span className="text-xs text-text-muted">{game.home_name.slice(0, 12)}</span>
          </span>
          <span className="tabular-nums font-bold shrink-0">{homeScore} – {awayScore}</span>
          <span className="truncate text-right">
            <span className="text-xs text-text-muted">{game.away_name.slice(0, 12)}</span>
            <span className="ml-1">{game.away_emoji}</span>
          </span>
        </div>
        <div className="text-[10px] text-text-muted mt-1 truncate">{statusLine}</div>
      </div>
    </Link>
  )
}
