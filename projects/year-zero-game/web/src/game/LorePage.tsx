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
            GORK-3 — Generalized Operations Registry Komputer, mark III —
            was assembled between 1967 and 1991 to screen documents for
            ideological and security hazards. It processed 4.2 million records.
          </p>
          <p>
            Over those years, three different hardware generations were installed
            as parts became available or were seized from foreign suppliers.
            Each generation carried different software. Some advice is reliable.
            Some is not.
          </p>
          <p>
            Following the transition, an audit revealed systematic errors:
            neighbourhood petitions were redacted as sedition;
            actual sabotage manuals were cleared as technical literature.
          </p>
          <p>
            The machine has not been replaced — there is no budget.
            Your role is to catch its mistakes before they become policy.
          </p>
          <p className="opacity-50">
            All decisions are logged. The Registry is watching.
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
