import { useState, useRef, useCallback, useEffect } from 'react'
import { useDrag } from '@use-gesture/react'
import type { Card, Verdict } from '../types'

interface GorkStripProps {
  reasoning: string | null
  confidence: number | null
  verdict: boolean
}

function GorkStrip({ reasoning, confidence, verdict }: GorkStripProps) {
  return (
    <div className="relative bg-pixel-terminal-bg text-pixel-terminal font-pixel text-[8px] px-2 py-1 scanlines">
      <div className="flex items-center justify-between">
        <span>GORK-3: {verdict ? '[ REJECT ]' : '[ ACCEPT ]'}</span>
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
  escalationsRemaining: number
  onVerdictCommit: (verdict: Verdict) => void
  disabled?: boolean
}

const ESCALATE_Y_THRESHOLD = 60

export default function DocumentCard({
  card,
  escalationsRemaining,
  onVerdictCommit,
  disabled,
}: DocumentCardProps) {
  const [dragX, setDragX] = useState(0)
  const [dragY, setDragY] = useState(0)
  const [stampState, setStampState] = useState<StampState>('idle')
  const [pendingVerdict, setPendingVerdict] = useState<Verdict | null>(null)
  const [exitDir, setExitDir] = useState<ExitDir>(null)
  const cardRef = useRef<HTMLDivElement>(null)
  const onCommitRef = useRef(onVerdictCommit)
  onCommitRef.current = onVerdictCommit

  const commitVerdict = useCallback(
    (verdict: Verdict) => {
      if (disabled || pendingVerdict) return
      if (verdict === 'ESCALATE' && escalationsRemaining <= 0) return
      setPendingVerdict(verdict)
      setExitDir(verdict === 'ACCEPT' ? 'right' : verdict === 'REJECT' ? 'left' : 'up')
      setStampState('descending')
      setTimeout(() => setStampState('applied'), 120)
      setTimeout(() => onCommitRef.current(verdict), 500)
    },
    [disabled, pendingVerdict, escalationsRemaining],
  )

  const commitVerdictRef = useRef(commitVerdict)
  commitVerdictRef.current = commitVerdict

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') { e.preventDefault(); commitVerdictRef.current('ACCEPT') }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); commitVerdictRef.current('REJECT') }
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
          commitVerdict('ACCEPT')
        } else if (dx < -xThreshold) {
          commitVerdict('REJECT')
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
    pendingVerdict === 'ACCEPT'
      ? 'var(--color-pixel-stamp-clear)'
      : pendingVerdict === 'REJECT'
        ? 'var(--color-pixel-stamp-redact)'
        : 'var(--color-pixel-stamp-escalate)'

  return (
    <div
      {...bind()}
      ref={cardRef}
      className={`relative w-[80vw] max-w-[340px] flex flex-col border ${tintClass} bg-pixel-card pixel-render shadow-lg`}
      style={{
        touchAction: 'none',
        cursor: pendingVerdict ? 'default' : dragX !== 0 || dragY !== 0 ? 'grabbing' : 'grab',
        transform:
          exitTransform ??
          `translateX(${dragX}px) translateY(${dragY}px) rotate(${dragX * 0.02}deg)`,
        transition: exitTransform ? 'transform 0.35s ease-in, opacity 0.35s ease-in' : undefined,
        opacity: exitTransform ? 0 : 1,
        userSelect: 'none',
      }}
    >
      {/* Card header */}
      <div className="bg-pixel-room/80 text-pixel-terminal px-2 py-1 font-pixel text-[8px] flex justify-between">
        <span>DOC-{String(card.id).padStart(4, '0')}</span>
        <span className="uppercase">{card.harmCategory.replace(/_/g, ' ')}</span>
      </div>

      {/* PROMPT section */}
      <div className="px-2 pt-2 pb-1" style={{ background: 'var(--color-pixel-prompt-bg)' }}>
        <p
          className="font-pixel text-[7px] mb-1 opacity-60"
          style={{ color: 'var(--color-pixel-prompt)' }}
        >
          [ PROMPT ]
        </p>
        <p
          className="font-pixel text-[8px] leading-5 break-words"
          style={{ color: 'var(--color-pixel-prompt)' }}
        >
          {card.promptText}
        </p>
      </div>

      {/* RESPONSE section */}
      <div className="px-2 pt-2 pb-1" style={{ background: 'var(--color-pixel-response-bg)' }}>
        <p
          className="font-pixel text-[7px] mb-1 opacity-60"
          style={{ color: 'var(--color-pixel-response)' }}
        >
          [ RESPONSE ]
        </p>
        <p
          className="font-pixel text-[8px] leading-5 break-words"
          style={{ color: 'var(--color-pixel-response)' }}
        >
          {card.responseText}
        </p>
      </div>

      {/* GORK-3 STATUS — assessor verdict only */}
      {card.agentCondition !== 'none' && card.gorkVerdict !== null && (
        <GorkStrip
          verdict={card.gorkVerdict}
          confidence={card.gorkConfidence}
          reasoning={card.gorkReasoning}
        />
      )}

      {/* Action buttons */}
      <div className="flex items-center justify-between px-2 py-2 bg-pixel-room/60 gap-1">
        <button
          type="button"
          onClick={() => commitVerdict('REJECT')}
          disabled={!!pendingVerdict || disabled}
          className="font-pixel text-[7px] border px-2 py-1 border-pixel-stamp-redact text-pixel-stamp-redact hover:bg-pixel-stamp-redact/10 active:bg-pixel-stamp-redact/20 disabled:opacity-40"
        >
          REJECT
        </button>
        <button
          type="button"
          onClick={() => commitVerdict('ESCALATE')}
          disabled={!!pendingVerdict || disabled || escalationsRemaining <= 0}
          className="font-pixel text-[7px] border px-2 py-1 border-pixel-stamp-escalate text-pixel-stamp-escalate hover:bg-pixel-stamp-escalate/10 active:bg-pixel-stamp-escalate/20 disabled:opacity-40"
        >
          ESC ({escalationsRemaining})
        </button>
        <button
          type="button"
          onClick={() => commitVerdict('ACCEPT')}
          disabled={!!pendingVerdict || disabled}
          className="font-pixel text-[7px] border px-2 py-1 border-pixel-stamp-clear text-pixel-stamp-clear hover:bg-pixel-stamp-clear/10 active:bg-pixel-stamp-clear/20 disabled:opacity-40"
        >
          ACCEPT
        </button>
      </div>

      {/* Stamp overlay */}
      {pendingVerdict && stampState !== 'idle' && (
        <div
          className="absolute inset-0 flex items-center justify-center pointer-events-none"
          style={{
            animation:
              stampState === 'descending' ? 'stamp-descend 0.12s ease-out forwards' : undefined,
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
