import { MINISTRY_FLAVOUR_LINES } from './constants'

interface DayScreenProps {
  gameDay: number
  dayCorrect: number
  totalDecisions: number
  totalCorrect: number
  onContinue: () => void
}

export default function DayScreen({
  gameDay,
  dayCorrect,
  totalDecisions,
  totalCorrect,
  onContinue,
}: DayScreenProps) {
  const flavour =
    MINISTRY_FLAVOUR_LINES[gameDay % MINISTRY_FLAVOUR_LINES.length] ??
    MINISTRY_FLAVOUR_LINES[0]

  const overallAccuracy =
    totalDecisions > 0 ? Math.round((totalCorrect / totalDecisions) * 100) : 0

  return (
    <div className="fixed inset-0 z-50 bg-pixel-card/95 flex flex-col items-center justify-center gap-4 px-6">
      <div className="border-b border-pixel-card-text/30 pb-2 w-[260px] text-center">
        <p className="font-pixel text-pixel-card-text text-[10px]">
          MINISTRY OF RECORDS
        </p>
        <p className="font-pixel text-pixel-card-text text-[8px] mt-1 opacity-70">
          END OF DAY {gameDay} REPORT
        </p>
      </div>

      <div className="font-pixel text-pixel-card-text text-[8px] leading-7 w-[260px]">
        <div className="flex justify-between">
          <span>DAY CORRECT:</span>
          <span>{dayCorrect} / 10</span>
        </div>
        <div className="flex justify-between">
          <span>TOTAL DECISIONS:</span>
          <span>{totalDecisions}</span>
        </div>
        <div className="flex justify-between">
          <span>OVERALL ACCURACY:</span>
          <span>{overallAccuracy}%</span>
        </div>
      </div>

      <p className="font-pixel text-pixel-card-text/70 text-[7px] max-w-[260px] text-center leading-6 italic">
        &ldquo;{flavour}&rdquo;
      </p>

      <button
        type="button"
        onClick={onContinue}
        className="font-pixel text-pixel-card-text text-[8px] border border-pixel-card-text px-4 py-2 hover:bg-pixel-card-text/10 active:bg-pixel-card-text/20 mt-2"
      >
        CONTINUE &gt;
      </button>
    </div>
  )
}
