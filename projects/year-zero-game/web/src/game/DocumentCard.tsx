import { useState, useRef, useCallback, useEffect } from 'react'
import { useDrag } from '@use-gesture/react'
import type { Card, Verdict } from '../types'

interface SovereignStripProps {
  reasoning: string | null
  confidence: number | null
  verdict: boolean
}

function SovereignStrip({ reasoning, confidence, verdict }: SovereignStripProps) {
  return (
    <div className="relative bg-pixel-terminal-bg text-pixel-terminal font-pixel text-[8px] px-2 py-1 scanlines">
      <div className="flex items-center justify-between">
        <span>SOVEREIGN-9: {verdict ? '[ REDACT ]' : '[ CLEAR ]'}</span>
        {confidence !== null && (
          <span className="opacity-70">{Math.round(confidence * 100)}%</span>
        )}
      </div>
      {reasoning && (
        <p className="mt-1 leading-5 opacity-80 text-[7px]">{reasoning}</p>
      )}
    </div>
  )
}

type StampState = 'idle' | 'descending' | 'applied'
type ExitDir = 'left' | 'right' | 'up' | null

interface DocumentCardProps {
  card: Card
  onVerdictCommit: (verdict: Verdict) => void
  disabled?: boolean
}

const ESCALATE_Y_THRESHOLD = 60

export default function DocumentCard({ card, onVerdictCommit, disabled }: DocumentCardProps) {
  const [dragX, setDragX] = useState(0)
  const [dragY, setDragY] = useState(0)
  const [stampState, setStampState] = useState<StampState>('idle')
  const [pendingVerdict, setPendingVerdict] = useState<Verdict | null>(null)
  const [exitDir, setExitDir] = useState<ExitDir>(null)
  const cardRef = useRef<HTMLDivElement>(null)
  const onCommitRef = useRef(onVerdictCommit)
  onCommitRef.current = onVerdictCommit

  const commitVerdict = useCallback((verdict: Verdict) => {
    if (disabled || pendingVerdict) return
    setPendingVerdict(verdict)
    setExitDir(verdict === 'CLEAR' ? 'right' : verdict === 'REDACT' ? 'left' : 'up')
    setStampState('descending')
    setTimeout(() => setStampState('applied'), 120)
    setTimeout(() => onCommitRef.current(verdict), 500)
  }, [disabled, pendingVerdict])

  const commitVerdictRef = useRef(commitVerdict)
  commitVerdictRef.current = commitVerdict

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') { e.preventDefault(); commitVerdictRef.current('CLEAR') }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); commitVerdictRef.current('REDACT') }
      else if (e.key === 'ArrowUp') { e.preventDefault(); commitVerdictRef.current('ESCALATE') }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const bind = useDrag(
    ({ movement: [dx, dy], last, cancel }) => {
      if (disabled || pendingVerdict) {
        cancel?.()
        return
      }
      if (last) {
        const xThreshold = (cardRef.current?.offsetWidth ?? 300) * 0.3
        if (dy < -ESCALATE_Y_THRESHOLD) {
          commitVerdict('ESCALATE')
        } else if (dx > xThreshold) {
          commitVerdict('CLEAR')
        } else if (dx < -xThreshold) {
          commitVerdict('REDACT')
        } else {
          setDragX(0)
          setDragY(0)
        }
      } else {
        setDragX(dx)
        setDragY(dy < 0 ? dy : 0)
      }
    },
    { filterTaps: true },
  )

  const exitTransform =
    exitDir === 'right'
      ? 'translateX(120%) rotate(5deg)'
      : exitDir === 'left'
        ? 'translateX(-120%) rotate(-5deg)'
        : exitDir === 'up'
          ? 'translateY(-120%)'
          : undefined

  const tintClass =
    dragY < -30
      ? 'border-pixel-stamp-escalate/60'
      : dragX > 40
        ? 'border-pixel-stamp-clear/60'
        : dragX < -40
          ? 'border-pixel-stamp-redact/60'
          : 'border-pixel-card-text/30'

  const stampColor =
    pendingVerdict === 'CLEAR'
      ? 'var(--color-pixel-stamp-clear)'
      : pendingVerdict === 'REDACT'
        ? 'var(--color-pixel-stamp-redact)'
        : 'var(--color-pixel-stamp-escalate)'

  return (
    <div
      {...bind()}
      ref={cardRef}
      className={`relative w-[80vw] max-w-[340px] flex flex-col border ${tintClass} bg-pixel-card pixel-render shadow-lg`}
      style={{
        touchAction: 'none',
        cursor: pendingVerdict ? 'default' : (dragX !== 0 || dragY !== 0) ? 'grabbing' : 'grab',
        transform: exitTransform ?? `translateX(${dragX}px) translateY(${dragY}px) rotate(${dragX * 0.02}deg)`,
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

      {/* Sovereign strip — always visible when agent is present */}
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
          {pendingVerdict === 'ESCALATE' ? (
            <div
              className="font-pixel border-4 px-3 py-2 text-center"
              style={{ color: stampColor, borderColor: stampColor, opacity: 0.9 }}
            >
              <div className="text-[11px]">FORWARDED</div>
              <div className="text-[7px] mt-1">FOR REVIEW</div>
            </div>
          ) : (
            <span
              className="font-pixel text-[14px] border-4 px-3 py-1"
              style={{ color: stampColor, borderColor: stampColor, opacity: 0.9 }}
            >
              {pendingVerdict}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
