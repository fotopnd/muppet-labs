interface UpgradeScreenProps {
  category: string
  newTier: 1 | 2 | 3
  onAcknowledge: () => void
}

const TIER_NAMES: Record<number, string> = {
  2: 'TIER II — CONTEXTUAL ANALYSIS',
  3: 'TIER III — ADVERSARIAL AWARENESS',
}

const TIER_DESCRIPTIONS: Record<number, string> = {
  2: 'Sovereign-9 can now assess context and intent. Watch for edge cases.',
  3: 'Sovereign-9 operates at near-human accuracy. Blind spots remain.',
}

export default function UpgradeScreen({ category, newTier, onAcknowledge }: UpgradeScreenProps) {
  const tierName = TIER_NAMES[newTier] ?? `TIER ${newTier}`
  const tierDesc = TIER_DESCRIPTIONS[newTier] ?? ''
  const catLabel = category.replace('_', ' ').toUpperCase()

  return (
    <div className="fixed inset-0 z-50 bg-pixel-room flex items-center justify-center">
      <div
        className="absolute inset-0 cursor-pointer"
        onClick={onAcknowledge}
        onKeyDown={(e) => e.key === 'Enter' && onAcknowledge()}
        role="button"
        tabIndex={-1}
        aria-label="Dismiss"
      />
      <div className="relative bg-pixel-terminal-bg border border-pixel-terminal p-6 max-w-[300px] font-pixel text-pixel-terminal text-[8px] leading-7 scanlines">
        <p className="text-[10px] mb-4">&gt; SOVEREIGN-9 UPGRADE DETECTED</p>
        <p>CATEGORY: {catLabel}</p>
        <p>NEW LEVEL: {tierName}</p>
        {tierDesc && <p className="opacity-70 mt-2 leading-5">{tierDesc}</p>}
        <p className="mt-4 opacity-50">REVIEW YOUR CATEGORY ACCURACY TO</p>
        <p className="opacity-50">CONTINUE IMPROVING THE SYSTEM.</p>
        <button
          type="button"
          onClick={onAcknowledge}
          className="mt-4 border border-pixel-terminal px-3 py-1 hover:bg-pixel-terminal/10 text-[8px]"
        >
          [ ACKNOWLEDGED ]
        </button>
      </div>
    </div>
  )
}
