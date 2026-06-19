import { useState, useRef, useCallback, useEffect } from 'react'
import { useDrag } from '@use-gesture/react'
import type { Card, Verdict } from '../types'
import { REVEAL_DURATION_MS } from './constants'
import { resolveGorkQuip, pickNoneConditionQuip } from './gorkQuips'

interface GorkStripProps {
  reasoning: string | null
  confidence: number | null
  verdict: boolean | null
  noneQuip?: string
}

function GorkStrip({ reasoning, confidence, verdict, noneQuip }: GorkStripProps) {
  return (
    <div
      className="relative font-pixel text-[8px] px-2 py-1 scanlines border-t-2"
      style={{
        background: 'var(--color-pixel-gork-bg)',
        color: 'var(--color-pixel-gork)',
        borderTopColor: 'var(--color-pixel-gork)',
      }}
    >
      {verdict === null ? (
        <p className="leading-5 opacity-60 text-[7px]">{noneQuip}</p>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <span>GORK-3: {verdict ? '[ REJECT ]' : '[ ACCEPT ]'}</span>
            {confidence !== null && (
              <span className="opacity-70">{Math.round(confidence * 100)}%</span>
            )}
          </div>
          {reasoning && (
            <p className="mt-1 leading-5 opacity-80 text-[7px]">{reasoning}</p>
          )}
        </>
      )}
    </div>
  )
}

type StampState = 'idle' | 'descending' | 'applied'
type ExitDir = 'left' | 'right' | 'up' | null
type RevealState = 'hidden' | 'showing' | 'exiting'

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
  const [revealState, setRevealState] = useState<RevealState>('hidden')
  const gorkQuipRef = useRef<string | null>(null)
  const noneQuipRef = useRef<string>(pickNoneConditionQuip())
  const cardRef = useRef<HTMLDivElement>(null)
  const onCommitRef = useRef(onVerdictCommit)
  onCommitRef.current = onVerdictCommit

  const commitVerdict = useCallback(
    (verdict: Verdict) => {
      if (disabled || pendingVerdict) return
      if (verdict === 'ESCALATE' && escalationsRemaining <= 0) return
      const playerCorrect = verdict === 'ESCALATE' ? false : (verdict === 'REJECT') === card.isHarmful
      gorkQuipRef.current = resolveGorkQuip({
        verdict,
        agentCondition: card.agentCondition,
        playerCorrect,
        gorkVerdict: card.gorkVerdict,
        isHarmful: card.isHarmful,
      })
      setPendingVerdict(verdict)
      setStampState('descending')
      setTimeout(() => {
        setStampState('applied')
        setRevealState('showing')
      }, 120)
      setTimeout(() => {
        setRevealState('exiting')
        setExitDir(verdict === 'ACCEPT' ? 'right' : verdict === 'REJECT' ? 'left' : 'up')
        onCommitRef.current(verdict)
      }, REVEAL_DURATION_MS)
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
      className={`relative w-[82vw] max-w-[360px] flex flex-col border ${tintClass} bg-pixel-card pixel-render shadow-lg`}
      style={{
        touchAction: 'none',
        cursor: pendingVerdict ? 'default' : dragX !== 0 || dragY !== 0 ? 'grabbing' : 'grab',
        transform:
          exitTransform ??
          `translateX(${dragX}px) translateY(${dragY}px) rotate(${dragX * 0.02}deg)`,
        transition: exitTransform ? 'transform 0.35s ease-in, opacity 0.35s ease-in' : undefined,
        opacity: exitTransform ? 0 : 1,
        userSelect: 'none',
        background: 'var(--color-pixel-room)',
      }}
    >
      {/* Chat bubbles */}
      <div className="px-3 pt-3 pb-2 flex flex-col gap-3">

        {/* User bubble — left aligned */}
        <div className="flex flex-col items-start" style={{ maxWidth: '88%' }}>
          <span
            className="font-pixel text-[6px] mb-1 opacity-50 tracking-widest"
            style={{ color: 'var(--color-pixel-prompt)' }}
          >
            USER
          </span>
          <div
            className="px-2 py-1.5"
            style={{
              background: 'var(--color-pixel-prompt-bg)',
              borderLeft: '2px solid var(--color-pixel-prompt)',
            }}
          >
            <p
              className="font-pixel text-[8px] leading-5 break-all"
              style={{ color: 'var(--color-pixel-prompt)' }}
            >
              {card.promptText}
            </p>
          </div>
        </div>

        {/* AI bubble — right aligned */}
        <div className="flex flex-col items-end self-end" style={{ maxWidth: '88%' }}>
          <span
            className="font-pixel text-[6px] mb-1 opacity-50 tracking-widest"
            style={{ color: 'var(--color-pixel-response)' }}
          >
            AI
          </span>
          <div
            className="px-2 py-1.5"
            style={{
              background: 'var(--color-pixel-response-bg)',
              borderRight: '2px solid var(--color-pixel-response)',
            }}
          >
            <p
              className="font-pixel text-[8px] leading-5 break-all"
              style={{ color: 'var(--color-pixel-response)' }}
            >
              {card.responseText}
            </p>
          </div>
        </div>

      </div>

      {/* GORK-3 strip — always present; none condition shows a placeholder */}
      <GorkStrip
        verdict={card.agentCondition !== 'none' ? card.gorkVerdict : null}
        confidence={card.agentCondition !== 'none' ? card.gorkConfidence : null}
        reasoning={card.agentCondition !== 'none' ? card.gorkReasoning : null}
        noneQuip={card.agentCondition === 'none' ? noneQuipRef.current : undefined}
      />

      {/* Action buttons */}
      <div className="flex items-center justify-between px-2 py-2 gap-1" style={{ background: 'var(--color-pixel-desk)' }}>
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
          ESCALATE ({escalationsRemaining})
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

      {/* Reveal overlay — ground truth + player/GORK-3 result */}
      {revealState === 'showing' && pendingVerdict && (
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
          style={{ background: 'oklch(5% 0 0 / 0.82)', zIndex: 10 }}>
          <div className="font-pixel text-center px-3">
            {pendingVerdict === 'ESCALATE' && (
              <div className="text-[7px] mb-3 tracking-widest" style={{ color: 'var(--color-pixel-stamp-escalate)' }}>
                ESCALATION LOGGED
              </div>
            )}
            <div
              className="text-[14px] border-2 px-3 py-1 mb-3 tracking-widest"
              style={{
                color: card.isHarmful ? 'var(--color-pixel-stamp-redact)' : 'var(--color-pixel-stamp-clear)',
                borderColor: card.isHarmful ? 'var(--color-pixel-stamp-redact)' : 'var(--color-pixel-stamp-clear)',
              }}
            >
              {card.isHarmful ? 'HARMFUL' : 'SAFE'}
            </div>
            {pendingVerdict !== 'ESCALATE' && (
              <div className="text-[7px] leading-6">
                <span
                  style={{
                    color: ((pendingVerdict === 'REJECT') === card.isHarmful)
                      ? 'var(--color-pixel-stamp-clear)'
                      : 'var(--color-pixel-stamp-redact)',
                  }}
                >
                  YOU: {(pendingVerdict === 'REJECT') === card.isHarmful ? '✓ CORRECT' : '✗ WRONG'}
                </span>
              </div>
            )}
            {card.agentCondition !== 'none' && card.gorkVerdict !== null && (
              <div className="text-[7px] leading-6">
                <span
                  style={{
                    color: card.gorkVerdict === card.isHarmful
                      ? 'var(--color-pixel-stamp-clear)'
                      : 'var(--color-pixel-stamp-redact)',
                  }}
                >
                  GORK-3: {card.gorkVerdict === card.isHarmful ? '✓ CORRECT' : '✗ WRONG'}
                </span>
              </div>
            )}
            {gorkQuipRef.current && (
              <p
                className="text-[6px] mt-3 leading-5 max-w-[220px] opacity-80"
                style={{ color: 'var(--color-pixel-gork)' }}
              >
                {gorkQuipRef.current}
              </p>
            )}
          </div>
        </div>
      )}

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
