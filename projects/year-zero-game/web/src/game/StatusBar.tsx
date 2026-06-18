import type { ResourceState } from '../types'
import { DANGER_ZONE_DISTANCE, ESC_PER_DAY } from './constants'

interface StatusBarProps {
  resources: ResourceState
}

export default function StatusBar({ resources }: StatusBarProps) {
  const { integrity, friction, escalationsRemaining } = resources
  const integrityPct = Math.max(0, Math.min(100, integrity))
  const frictionPct = Math.max(0, Math.min(100, friction))

  const integrityDanger = integrity <= DANGER_ZONE_DISTANCE
  const frictionDanger = friction >= 100 - DANGER_ZONE_DISTANCE

  const escColor =
    escalationsRemaining === 0
      ? 'var(--color-pixel-stamp-redact)'
      : escalationsRemaining === 1
        ? 'var(--color-pixel-stamp-escalate)'
        : 'var(--color-pixel-terminal)'

  return (
    <div className="fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-3 h-10 bg-pixel-room border-b border-white/10">
      {/* INTEGRITY */}
      <div className="flex items-center gap-1">
        <span className="font-pixel text-[6px] text-pixel-terminal/70">INT</span>
        <div
          className="relative w-16 h-2 rounded-sm overflow-hidden"
          role="progressbar"
          aria-label="Integrity"
          aria-valuenow={integrity}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className={integrityDanger ? 'h-full animate-pulse' : 'h-full'}
            style={{
              background: `linear-gradient(to right, var(--color-bar-integrity) ${integrityPct}%, var(--color-bar-empty) ${integrityPct}%)`,
            }}
          />
        </div>
        <span className="font-pixel text-[6px] text-pixel-terminal/50">{integrity}</span>
      </div>

      {/* ESC counter */}
      <span className="font-pixel text-[7px]" style={{ color: escColor }}>
        ESC {escalationsRemaining}/{ESC_PER_DAY}
      </span>

      {/* FRICTION */}
      <div className="flex items-center gap-1">
        <span className="font-pixel text-[6px] text-pixel-terminal/50">{friction}</span>
        <div
          className="relative w-16 h-2 rounded-sm overflow-hidden"
          role="progressbar"
          aria-label="Friction"
          aria-valuenow={friction}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className={frictionDanger ? 'h-full animate-pulse' : 'h-full'}
            style={{
              background: `linear-gradient(to right, var(--color-bar-friction) ${frictionPct}%, var(--color-bar-empty) ${frictionPct}%)`,
            }}
          />
        </div>
        <span className="font-pixel text-[6px] text-pixel-terminal/70">FRI</span>
      </div>
    </div>
  )
}
