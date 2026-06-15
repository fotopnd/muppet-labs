interface LorePageProps {
  onContinue: () => void
}

export default function LorePage({ onContinue }: LorePageProps) {
  return (
    <div className="fixed inset-0 z-50 bg-pixel-room flex flex-col items-center justify-center gap-6 px-6 overflow-y-auto py-12">
      <div className="max-w-[300px] w-full">
        <p className="font-pixel text-pixel-terminal text-[8px] mb-4">
          REGISTRY BRIEFING — EYES ONLY
        </p>

        <div className="font-pixel text-pixel-card/80 text-[7px] leading-6 space-y-4">
          <p>
            Sovereign-9 was developed between 1971 and 1989 to screen documents
            for ideological hazards. It processed 4.2 million records.
          </p>
          <p>
            Following the transition, an audit revealed systematic errors:
            neighbourhood petitions were redacted as sedition;
            actual sabotage manuals were cleared as technical literature.
          </p>
          <p>
            The machine has been partially retrained. But it still makes mistakes.
            Your role is to catch them.
          </p>
          <p>
            You will review documents across five harm categories:
            VIOLENCE, HATE SPEECH, PII EXPOSURE, CYBERCRIME, SEXUAL CONTENT.
          </p>
          <p>
            As you build expertise in a category, Sovereign-9&apos;s assistance
            will improve. But it will never be perfect.
          </p>
          <p className="opacity-50">
            This system is being monitored. All decisions are logged.
          </p>
        </div>

        <button
          type="button"
          onClick={onContinue}
          className="font-pixel text-pixel-terminal text-[8px] border border-pixel-terminal px-4 py-2 hover:bg-pixel-terminal/10 mt-6 w-full"
        >
          BEGIN DAY 1 &gt;
        </button>
      </div>
    </div>
  )
}
