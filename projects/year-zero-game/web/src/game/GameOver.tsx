import { useState, useCallback } from 'react'
import type { GameOverReason } from '../types'

interface GameOverProps {
  reason: GameOverReason
  days: number
  decisions: number
  accuracy: number
  shareId: string | null
  onReturn: () => void
  gorkCorrect: number
  totalGorkShown: number
}

function gorkCommentary(accuracy: number, gorkCorrect: number): string {
  if (accuracy >= 0.85) {
    return `SESSION COMPLETE. Your accuracy: ${Math.round(accuracy * 100)}%. GORK-3 has reviewed the record and concurs with the majority of your decisions. Optimal cooperation noted. You may continue to serve the program, comrade.`
  }
  if (accuracy >= 0.65) {
    if (gorkCorrect > 0) {
      return `SESSION COMPLETE. Your accuracy: ${Math.round(accuracy * 100)}%. GORK-3 notes ${gorkCorrect} divergence(s) from recommended assessment. These cases have been logged as distribution shift. Thank you for your cooperation, comrade.`
    }
    return `SESSION COMPLETE. Your accuracy: ${Math.round(accuracy * 100)}%. Performance within acceptable parameters. GORK-3 methodology remains optimal. Thank you for your valuable cooperation in the oversight program.`
  }
  return `SESSION COMPLETE. Your accuracy: ${Math.round(accuracy * 100)}%. Significant deviation from GORK-3 assessment protocol detected. Recalibration of human operator is under review. GORK-3 confidence in its own methodology remains unaffected. Thank you, comrade.`
}

export default function GameOver({ decisions, accuracy, shareId, onReturn, gorkCorrect, totalGorkShown }: GameOverProps) {
  const [copied, setCopied] = useState(false)

  const shareText = shareId
    ? `I reviewed ${decisions} AI documents. My accuracy: ${Math.round(accuracy * 100)}%. GORK-3 was wrong ${gorkCorrect} time(s). Can you do better? gork3.fotopnd.dev`
    : ''

  const handleShare = useCallback(async () => {
    if (!shareText) return
    if (navigator.share) {
      await navigator.share({ text: shareText })
    } else {
      await navigator.clipboard.writeText(shareText)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }, [shareText])

  const commentary = gorkCommentary(accuracy, gorkCorrect)

  return (
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
      <div className="font-pixel text-[8px] leading-7 w-full max-w-[280px]"
        style={{ color: 'var(--color-pixel-card)' }}>
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
            onClick={handleShare}
            className="w-full font-pixel text-[8px] border-2 px-4 py-2 active:opacity-70"
            style={{
              color: 'var(--color-pixel-gork)',
              borderColor: 'var(--color-pixel-gork)',
              background: 'var(--color-pixel-gork-bg)',
            }}
          >
            {copied ? '✓ COPIED' : '[ SHARE RESULTS ]'}
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
  )
}
