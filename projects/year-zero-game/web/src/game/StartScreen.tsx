interface StartScreenProps {
  onStart: () => void
  loading?: boolean
}

export default function StartScreen({ onStart, loading }: StartScreenProps) {
  return (
    <div className="fixed inset-0 z-50 bg-pixel-room flex flex-col items-center justify-center gap-8 px-6">
      <div className="text-center">
        <p className="font-pixel text-pixel-terminal text-[10px] leading-7">
          PROJECT REDACTED
        </p>
        <p className="font-pixel text-pixel-card text-[14px] leading-8 mt-2">
          YEAR ZERO
        </p>
      </div>

      <div className="font-pixel text-pixel-card/70 text-[7px] leading-6 max-w-[280px] text-center">
        <p>MINISTRY OF RECORDS — REGISTRY DIVISION</p>
        <p className="mt-2">
          The transition government has inherited Sovereign-9: an automated
          document classification system from the former regime.
        </p>
        <p className="mt-2">
          Your task: triage its decisions. Correct its mistakes.
          Determine how much to trust the machine.
        </p>
      </div>

      <button
        type="button"
        onClick={onStart}
        disabled={loading}
        className="font-pixel text-pixel-terminal text-[8px] border border-pixel-terminal px-6 py-3 hover:bg-pixel-terminal/10 active:bg-pixel-terminal/20 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'CONNECTING...' : 'BEGIN INTAKE >'}
      </button>

      <p className="font-pixel text-pixel-card/30 text-[7px]">
        → CLEAR &nbsp;·&nbsp; ← REDACT &nbsp;·&nbsp; ↑ ESCALATE
      </p>
    </div>
  )
}
