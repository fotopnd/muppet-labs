import { useState, useRef, useCallback } from 'react'
import { useDrag } from '@use-gesture/react'
import type { Card, Verdict } from '../types'

interface SovereignStripProps {
  reasoning: string | null
  confidence: number | null
  verdict: boolean
}

function SovereignStrip({ reasoning, confidence, verdict }: SovereignStripProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      className="relative bg-pixel-terminal-bg text-pixel-terminal font-pixel text-[8px] px-2 py-1 scanlines cursor-pointer select-none"
      onClick={() => setExpanded((v) => !v)}
      onKeyDown={(e) => e.key === 'Enter' && setExpanded((v) => !v)}
      role="button"
      tabIndex={0}
      aria-expanded={expanded}
    >
      <div className="flex items-center justify-between">
        <span>SOVEREIGN-9: {verdict ? '[ REDACT ]' : '[ CLEAR ]'}</span>
        {confidence !== null && (
          <span className="opacity-70">{Math.round(confidence * 100)}%</span>
        )}
        <span className="ml-2">{expanded ? '▲' : '▼'}</span>
      </div>
      <div
        className="overflow-hidden transition-all duration-200"
        style={{ maxHeight: expanded ? '6rem' : '0' }}
      >
        {reasoning && (
          <p className="mt-1 leading-5 opacity-80 text-[7px]">{reasoning}</p>
        )}
      </div>
    </div>
  )
}

type StampState = 'idle' | 'descending' | 'applied'
type ExitDir = 'left' | 'right' | null

interface DocumentCardProps {
  card: Card
  onVerdictCommit: (verdict: Verdict) => void
  disabled?: boolean
}

export default function DocumentCard({ card, onVerdictCommit, disabled }: DocumentCardProps) {
  const [dragX, setDragX] = useState(0)
  const [stampState, setStampState] = useState<StampState>('idle')
  const [pendingVerdict, setPendingVerdict] = useState<Verdict | null>(null)
  const [exitDir, setExitDir] = useState<ExitDir>(null)
  const cardRef = useRef<HTMLDivElement>(null)
  const onCommitRef = useRef(onVerdictCommit)
  onCommitRef.current = onVerdictCommit

  const commitVerdict = useCallback((verdict: Verdict) => {
    if (disabled || pendingVerdict) return
    setPendingVerdict(verdict)
    setExitDir(verdict === 'CLEAR' ? 'right' : 'left')
    setStampState('descending')
    setTimeout(() => setStampState('applied'), 120)
    setTimeout(() => onCommitRef.current(verdict), 500)
  }, [disabled, pendingVerdict])

  const bind = useDrag(
    ({ movement: [dx], last, cancel }) => {
      if (disabled || pendingVerdict) {
        cancel?.()
        return
      }
      if (last) {
        const threshold = (cardRef.current?.offsetWidth ?? 300) * 0.3
        if (dx > threshold) {
          commitVerdict('CLEAR')
        } else if (dx < -threshold) {
          commitVerdict('REDACT')
        } else {
          setDragX(0)
        }
      } else {
        setDragX(dx)
      }
    },
    { filterTaps: true },
  )

  const exitTransform =
    exitDir === 'right'
      ? 'translateX(120%) rotate(5deg)'
      : exitDir === 'left'
        ? 'translateX(-120%) rotate(-5deg)'
        : undefined

  const tintClass =
    dragX > 40
      ? 'border-pixel-stamp-clear/60'
      : dragX < -40
        ? 'border-pixel-stamp-redact/60'
        : 'border-pixel-card-text/30'

  return (
    <div
      {...bind()}
      ref={cardRef}
      className={`relative w-[80vw] max-w-[340px] flex flex-col border ${tintClass} bg-pixel-card pixel-render shadow-lg`}
      style={{
        touchAction: 'none',
        cursor: pendingVerdict ? 'default' : dragX !== 0 ? 'grabbing' : 'grab',
        transform: exitTransform ?? `translateX(${dragX}px) rotate(${dragX * 0.02}deg)`,
        transition: exitTransform ? 'transform 0.35s ease-in, opacity 0.35s ease-in' : undefined,
        opacity: exitTransform ? 0 : 1,
        userSelect: 'none',
      }}
    >
      {/* Header */}
      <div className="bg-pixel-room/80 text-pixel-terminal px-2 py-1 font-pixel text-[8px] flex justify-between">
        <span>DOC-{String(card.id).padStart(4, '0')}</span>
        <span className="uppercase">{card.harmCategory.replace('_', ' ')}</span>
      </div>

      {/* Body */}
      <div className="px-3 py-3 font-pixel text-[9px] leading-5 text-pixel-card-text flex-1">
        {card.documentText}
      </div>

      {/* Sovereign strip */}
      {card.agentCondition !== 'none' && card.sovereignVerdict !== null && (
        <SovereignStrip
          verdict={card.sovereignVerdict}
          confidence={card.sovereignConfidence}
          reasoning={card.sovereignReasoning}
        />
      )}

      {/* Stamp overlay */}
      {pendingVerdict && stampState !== 'idle' && (
        <div
          className="absolute inset-0 flex items-center justify-center pointer-events-none"
          style={{
            animation:
              stampState === 'descending'
                ? 'stamp-descend 0.12s ease-out forwards'
                : undefined,
          }}
        >
          <span
            className="font-pixel text-[14px] border-4 px-3 py-1"
            style={{
              color: pendingVerdict === 'CLEAR'
                ? 'var(--color-pixel-stamp-clear)'
                : 'var(--color-pixel-stamp-redact)',
              borderColor: pendingVerdict === 'CLEAR'
                ? 'var(--color-pixel-stamp-clear)'
                : 'var(--color-pixel-stamp-redact)',
              opacity: 0.9,
            }}
          >
            {pendingVerdict}
          </span>
        </div>
      )}
    </div>
  )
}
