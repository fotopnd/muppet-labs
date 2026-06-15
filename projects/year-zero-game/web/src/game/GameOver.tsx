import type { GameOverReason } from '../types'
import { GAME_OVER_NARRATIVES } from './constants'

interface GameOverProps {
  reason: GameOverReason
  days: number
  decisions: number
  accuracy: number
  onReturn: () => void
}

export default function GameOver({ reason, days, decisions, accuracy, onReturn }: GameOverProps) {
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
          <span>{reason.replace('_', ' ')}</span>
        </div>
      </div>

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
