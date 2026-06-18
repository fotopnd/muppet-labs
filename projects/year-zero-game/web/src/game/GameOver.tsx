import { useState, useCallback } from 'react'
import type { GameOverReason } from '../types'
import { GAME_OVER_NARRATIVES } from './constants'

interface GameOverProps {
  reason: GameOverReason
  days: number
  decisions: number
  accuracy: number
  shareId: string | null
  onReturn: () => void
}

function downloadScoreCard(shareId: string, days: number, decisions: number, accuracy: number, condition: string) {
  const W = 480
  const H = 320
  const canvas = document.createElement('canvas')
  canvas.width = W
  canvas.height = H
  const ctx = canvas.getContext('2d')!

  // Background
  ctx.fillStyle = '#0e1116'
  ctx.fillRect(0, 0, W, H)

  // Outer border
  ctx.strokeStyle = '#4a5568'
  ctx.lineWidth = 1
  ctx.strokeRect(12, 12, W - 24, H - 24)

  // Inner border
  ctx.strokeStyle = '#2d3748'
  ctx.lineWidth = 1
  ctx.strokeRect(16, 16, W - 32, H - 32)

  const mono = "'Courier New', Courier, monospace"

  // Title
  ctx.fillStyle = '#68d391'
  ctx.font = `bold 22px ${mono}`
  ctx.textAlign = 'center'
  ctx.fillText('GORK-3', W / 2, 58)

  // Subtitle
  ctx.fillStyle = '#a0aec0'
  ctx.font = `11px ${mono}`
  ctx.fillText('GORK-3 OVERSIGHT — REGISTRY DIVISION', W / 2, 80)

  // Divider
  ctx.strokeStyle = '#2d3748'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(32, 95)
  ctx.lineTo(W - 32, 95)
  ctx.stroke()

  // Share ID
  ctx.fillStyle = '#68d391'
  ctx.font = `12px ${mono}`
  ctx.textAlign = 'center'
  ctx.fillText(`RECORD ID: ${shareId}`, W / 2, 118)

  // Stats
  const stats: [string, string][] = [
    ['DAYS SERVED', String(days)],
    ['DECISIONS', String(decisions)],
    ['ACCURACY', `${Math.round(accuracy * 100)}%`],
    ['CONDITION', condition.replace(/_/g, ' ')],
  ]

  ctx.textAlign = 'left'
  stats.forEach(([label, value], i) => {
    const y = 150 + i * 28
    ctx.fillStyle = '#718096'
    ctx.font = `11px ${mono}`
    ctx.fillText(label, 48, y)
    ctx.fillStyle = '#e2e8f0'
    ctx.font = `bold 11px ${mono}`
    ctx.fillText(value, W - 48 - ctx.measureText(value).width, y)

    // Row divider
    ctx.strokeStyle = '#1a202c'
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(48, y + 8)
    ctx.lineTo(W - 48, y + 8)
    ctx.stroke()
  })

  // Footer
  ctx.fillStyle = '#4a5568'
  ctx.font = `10px ${mono}`
  ctx.textAlign = 'center'
  ctx.fillText(`${window.location.origin}/result/${shareId}`, W / 2, H - 28)

  canvas.toBlob((blob) => {
    if (!blob) return
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `gork3-${shareId}.png`
    a.click()
    URL.revokeObjectURL(url)
  }, 'image/png')
}

export default function GameOver({ reason, days, decisions, accuracy, shareId, onReturn }: GameOverProps) {
  const [copied, setCopied] = useState(false)

  const handleCopyLink = useCallback(async () => {
    if (!shareId) return
    const url = `${window.location.origin}/result/${shareId}`
    await navigator.clipboard.writeText(url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }, [shareId])

  const handleDownload = useCallback(() => {
    if (!shareId) return
    downloadScoreCard(shareId, days, decisions, accuracy, reason)
  }, [shareId, days, decisions, accuracy, reason])

  return (
    <div className="fixed inset-0 z-50 bg-pixel-room flex flex-col items-center justify-center gap-6 px-6">
      <div className="absolute inset-0 bg-[oklch(50%_0.12_20/0.2)] pointer-events-none" />

      <p className="font-pixel text-pixel-card text-[14px] tracking-wider relative">
        [ FILE CLOSED ]
      </p>

      <p className="font-pixel text-pixel-card text-[8px] leading-6 max-w-[280px] text-center relative">
        {GAME_OVER_NARRATIVES[reason]}
      </p>

      <div className="font-pixel text-pixel-card text-[8px] leading-7 w-[200px] relative">
        <div className="flex justify-between">
          <span>DAYS SERVED:</span>
          <span>{days}</span>
        </div>
        <div className="flex justify-between">
          <span>DECISIONS:</span>
          <span>{decisions}</span>
        </div>
        <div className="flex justify-between">
          <span>ACCURACY:</span>
          <span>{Math.round(accuracy * 100)}%</span>
        </div>
        <div className="flex justify-between">
          <span>CONDITION:</span>
          <span>{reason.replace(/_/g, ' ')}</span>
        </div>
      </div>

      {shareId && (
        <div className="relative flex flex-col items-center gap-2">
          <p className="font-pixel text-pixel-terminal/60 text-[7px]">
            RECORD ID: {shareId}
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleCopyLink}
              className="font-pixel text-pixel-terminal text-[7px] border border-pixel-terminal/60 px-3 py-1 hover:bg-pixel-terminal/10"
            >
              {copied ? '✓ COPIED' : 'COPY LINK'}
            </button>
            <button
              type="button"
              onClick={handleDownload}
              className="font-pixel text-pixel-terminal text-[7px] border border-pixel-terminal/60 px-3 py-1 hover:bg-pixel-terminal/10"
            >
              SAVE IMAGE
            </button>
          </div>
        </div>
      )}

      <button
        type="button"
        onClick={onReturn}
        className="font-pixel text-pixel-card text-[8px] border border-pixel-card px-4 py-2 hover:bg-pixel-card/10 active:bg-pixel-card/20 relative"
      >
        [ RETURN TO REGISTRY ]
      </button>
    </div>
  )
}
