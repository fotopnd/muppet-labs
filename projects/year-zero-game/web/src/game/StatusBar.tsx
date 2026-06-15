import type { BarState } from '../types'
import { DANGER_ZONE_DISTANCE, GAME_OVER_THRESHOLDS } from './constants'

interface BarUnitProps {
  label: string
  emoji: string
  value: number
  colorVar: string
  thresholds: Array<{ direction: 'min' | 'max'; value: number }>
}

function isInDangerZone(
  value: number,
  thresholds: Array<{ direction: 'min' | 'max'; value: number }>,
): boolean {
  return thresholds.some((t) => {
    if (t.direction === 'min') return value <= t.value + DANGER_ZONE_DISTANCE
    return value >= t.value - DANGER_ZONE_DISTANCE
  })
}

function BarUnit({ label, emoji, value, colorVar, thresholds }: BarUnitProps) {
  const pct = Math.max(0, Math.min(100, value))
  const danger = isInDangerZone(value, thresholds)

  return (
    <div className="flex items-center gap-1">
      <span className="text-[10px] leading-none" aria-hidden="true">{emoji}</span>
      <div
        className="relative w-10 h-2 rounded-sm overflow-hidden"
        role="progressbar"
        aria-label={label}
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className={danger ? 'h-full animate-pulse' : 'h-full'}
          style={{
            background: `linear-gradient(to right, var(${colorVar}) ${pct}%, var(--color-bar-empty) ${pct}%)`,
          }}
        />
        {/* Centre pip on compliance bar */}
        {colorVar === '--color-bar-compliance' && (
          <div className="absolute left-1/2 top-0 bottom-0 w-px bg-white/60" />
        )}
      </div>
    </div>
  )
}

interface StatusBarProps {
  bars: BarState
}

const BAR_CONFIG: Array<{
  key: keyof BarState
  label: string
  emoji: string
  colorVar: string
}> = [
  { key: 'publicTrust', label: 'Public Trust',  emoji: '👥', colorVar: '--color-bar-trust' },
  { key: 'security',    label: 'Security',       emoji: '🔒', colorVar: '--color-bar-security' },
  { key: 'treasury',    label: 'Treasury',       emoji: '💰', colorVar: '--color-bar-treasury' },
  { key: 'legitimacy',  label: 'Legitimacy',     emoji: '⚖️', colorVar: '--color-bar-legitimacy' },
  { key: 'compliance',  label: 'Compliance',     emoji: '📋', colorVar: '--color-bar-compliance' },
]

export default function StatusBar({ bars }: StatusBarProps) {
  return (
    <div className="fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-2 h-12 bg-pixel-room border-b border-white/10">
      {BAR_CONFIG.map(({ key, label, emoji, colorVar }) => (
        <BarUnit
          key={key}
          label={label}
          emoji={emoji}
          value={bars[key]}
          colorVar={colorVar}
          thresholds={GAME_OVER_THRESHOLDS[key].map((t) => ({
            direction: t.direction,
            value: t.value,
          }))}
        />
      ))}
    </div>
  )
}
