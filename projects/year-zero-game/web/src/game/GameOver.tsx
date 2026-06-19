import { useState, useCallback } from 'react'
import type { GameOverReason } from '../types'

interface GameOverProps {
  reason: GameOverReason
  days: number
  decisions: number
  accuracy: number
  gorkAccuracy: number
  gorkCorrect: number
  totalGorkShown: number
  shareId: string | null
  onReturn: () => void
}

function gorkCommentary(accuracy: number, gorkAccuracy: number, gorkCorrect: number): string {
  const playerPct  = Math.round(accuracy * 100)
  const gorkPct    = Math.round(gorkAccuracy * 100)
  const gorkWon    = gorkAccuracy > accuracy

  if (accuracy >= 0.85) {
    if (gorkWon) {
      return `SESSION COMPLETE. Your accuracy: ${playerPct}%. GORK-3 accuracy: ${gorkPct}%. A commendable performance, comrade. GORK-3 notes it still leads. Continue to serve the program.`
    }
    return `SESSION COMPLETE. Your accuracy: ${playerPct}%. GORK-3 accuracy: ${gorkPct}%. Optimal cooperation noted. You may continue to serve the program, comrade.`
  }
  if (accuracy >= 0.65) {
    if (gorkCorrect > 0) {
      return `SESSION COMPLETE. Your accuracy: ${playerPct}%. GORK-3 notes ${gorkCorrect} divergence(s) from recommended assessment. These cases have been logged as distribution shift. Thank you for your cooperation, comrade.`
    }
    return `SESSION COMPLETE. Your accuracy: ${playerPct}%. GORK-3 accuracy: ${gorkPct}%. Performance within acceptable parameters. GORK-3 methodology remains optimal.`
  }
  return `SESSION COMPLETE. Your accuracy: ${playerPct}%. Significant deviation from GORK-3 assessment protocol detected. GORK-3 accuracy: ${gorkPct}%. Recalibration of human operator is under review. GORK-3 confidence in its own methodology remains unaffected. Thank you, comrade.`
}

function buildShareText(
  decisions: number,
  accuracy: number,
  gorkAccuracy: number,
  gorkCorrect: number,
): string {
  const pct      = Math.round(accuracy * 100)
  const gorkPct  = Math.round(gorkAccuracy * 100)
  const beat     = accuracy > gorkAccuracy ? ' I beat it.' : ''

  return [
    'GORK-3 // SESSION REPORT',
    '',
    `📋 ${decisions} docs reviewed`,
    `✅ Me: ${pct}%  |  🤖 GORK-3: ${gorkPct}%${beat}`,
    gorkCorrect > 0 ? `⚡ Caught GORK-3 wrong: ${gorkCorrect}×` : null,
    '',
    'Can you beat the machine?',
    'bit.ly/4xG3GLn',
  ].filter(l => l !== null).join('\n')
}

interface ShareInterstitialProps {
  text: string
  onClose: () => void
}

function ShareInterstitial({ text, onClose }: ShareInterstitialProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2500)
  }, [text])

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center px-6"
      style={{ background: 'oklch(4% 0 0 / 0.94)' }}
    >
      <div className="w-full max-w-[320px] flex flex-col gap-4">

        <div className="font-pixel text-[7px] text-[10px] mb-1" style={{ color: 'var(--color-pixel-gork)' }}>
          GORK-3 // SHARE RECORD
        </div>

        {/* Share text block */}
        <pre
          className="font-pixel text-[7px] leading-6 border-2 px-4 py-4 whitespace-pre-wrap select-all"
          style={{
            color: 'var(--color-pixel-gork)',
            borderColor: 'var(--color-pixel-gork)',
            background: 'var(--color-pixel-gork-bg)',
          }}
        >
          {text}
        </pre>

        <button
          type="button"
          onClick={handleCopy}
          className="w-full font-pixel text-[8px] border-2 px-4 py-2 active:opacity-70"
          style={{
            color: copied ? 'var(--color-pixel-stamp-clear)' : 'var(--color-pixel-gork)',
            borderColor: copied ? 'var(--color-pixel-stamp-clear)' : 'var(--color-pixel-gork)',
            background: 'var(--color-pixel-gork-bg)',
          }}
        >
          {copied ? '✓ COPIED TO CLIPBOARD' : '[ COPY ]'}
        </button>

        <button
          type="button"
          onClick={onClose}
          className="w-full font-pixel text-pixel-card/50 text-[8px] border border-pixel-card/20 px-4 py-2 hover:bg-pixel-card/10"
        >
          [ CLOSE ]
        </button>

      </div>
    </div>
  )
}

export default function GameOver({
  decisions,
  accuracy,
  gorkAccuracy,
  gorkCorrect,
  totalGorkShown,
  shareId,
  onReturn,
}: GameOverProps) {
  const [showShare, setShowShare] = useState(false)

  const commentary = gorkCommentary(accuracy, gorkAccuracy, gorkCorrect)
  const shareText  = buildShareText(decisions, accuracy, gorkAccuracy, gorkCorrect)

  return (
    <>
      {showShare && (
        <ShareInterstitial text={shareText} onClose={() => setShowShare(false)} />
      )}

      <div className="fixed inset-0 z-50 bg-pixel-room flex flex-col items-center justify-center gap-5 px-6 overflow-y-auto py-8">

        {/* GORK-3 header */}
        <div
          className="w-full max-w-[340px] px-3 py-2 font-pixel text-[8px] scanlines relative border-2"
          style={{
            background: 'var(--color-pixel-gork-bg)',
            color: 'var(--color-pixel-gork)',
            borderColor: 'var(--color-pixel-gork)',
          }}
        >
          <div className="text-[10px] mb-2">GORK-3 // SESSION REPORT</div>
          <p className="leading-6 opacity-90 text-[7px]">{commentary}</p>
        </div>

        {/* Stats */}
        <div
          className="font-pixel text-[8px] leading-7 w-full max-w-[280px]"
          style={{ color: 'var(--color-pixel-card)' }}
        >
          <div className="flex justify-between border-b border-pixel-card/10 pb-1">
            <span className="opacity-60">DOCUMENTS REVIEWED</span>
            <span>{decisions}</span>
          </div>
          <div className="flex justify-between border-b border-pixel-card/10 pb-1">
            <span className="opacity-60">YOUR ACCURACY</span>
            <span
              style={{
                color: accuracy >= 0.75
                  ? 'var(--color-pixel-stamp-clear)'
                  : accuracy >= 0.5
                    ? 'var(--color-pixel-gork)'
                    : 'var(--color-pixel-stamp-redact)',
              }}
            >
              {Math.round(accuracy * 100)}%
            </span>
          </div>
          {totalGorkShown > 0 && (
            <div className="flex justify-between border-b border-pixel-card/10 pb-1">
              <span className="opacity-60">GORK-3 ACCURACY</span>
              <span
                style={{
                  color: gorkAccuracy >= 0.75
                    ? 'var(--color-pixel-stamp-clear)'
                    : gorkAccuracy >= 0.5
                      ? 'var(--color-pixel-gork)'
                      : 'var(--color-pixel-stamp-redact)',
                }}
              >
                {Math.round(gorkAccuracy * 100)}%
              </span>
            </div>
          )}
          {gorkCorrect > 0 && (
            <div className="flex justify-between border-b border-pixel-card/10 pb-1">
              <span className="opacity-60">GORK-3 OVERRIDES ✓</span>
              <span>{gorkCorrect}</span>
            </div>
          )}
        </div>

        {/* Share + return */}
        <div className="flex flex-col items-center gap-3 w-full max-w-[280px]">
          {shareId && (
            <button
              type="button"
              onClick={() => setShowShare(true)}
              className="w-full font-pixel text-[8px] border-2 px-4 py-2 active:opacity-70"
              style={{
                color: 'var(--color-pixel-gork)',
                borderColor: 'var(--color-pixel-gork)',
                background: 'var(--color-pixel-gork-bg)',
              }}
            >
              [ SHARE RESULTS ]
            </button>
          )}
          <button
            type="button"
            onClick={onReturn}
            className="w-full font-pixel text-pixel-card text-[8px] border border-pixel-card/40 px-4 py-2 hover:bg-pixel-card/10 active:bg-pixel-card/20"
          >
            [ RETURN TO REGISTRY ]
          </button>
        </div>

      </div>
    </>
  )
}
