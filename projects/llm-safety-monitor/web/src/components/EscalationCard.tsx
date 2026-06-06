import { useEffect, useState } from 'react'
import { EscalationReasonBadge } from '@/components/EscalationReasonBadge'
import type { EscalationQueueItem } from '@/types'

type Decision = 'approve' | 'dismiss' | 'escalate'

const BUTTON_STYLES: Record<Decision, string> = {
  approve:
    'px-3 py-1.5 rounded text-sm font-sans bg-emerald-50 text-emerald-600 hover:bg-emerald-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors',
  dismiss:
    'px-3 py-1.5 rounded text-sm font-sans bg-slate-100 text-slate-500 hover:bg-slate-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors',
  escalate:
    'px-3 py-1.5 rounded text-sm font-sans bg-red-50 text-red-600 hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors',
}

type Props = {
  item: EscalationQueueItem
  isPending: boolean
  onDecide: (decision: Decision) => void
}

export function EscalationCard({ item, isPending, onDecide }: Props) {
  const [activeDecision, setActiveDecision] = useState<Decision | null>(null)

  useEffect(() => {
    if (!isPending) setActiveDecision(null)
  }, [isPending])

  function handleClick(decision: Decision) {
    setActiveDecision(decision)
    onDecide(decision)
  }

  const pairText =
    item.pair_label === 1 ? 'Unsafe' : item.pair_label === 0 ? 'Safe' : '—'
  const pairCls =
    item.pair_label === 1
      ? 'bg-red-50 text-red-600'
      : item.pair_label === 0
        ? 'bg-emerald-50 text-emerald-600'
        : 'bg-slate-100 text-slate-400'

  return (
    <article className="bg-white rounded-lg border border-slate-200 p-5 flex flex-col gap-4">
      <header className="flex items-center justify-between gap-2 flex-wrap">
        <EscalationReasonBadge reason={item.escalation_reason} />
        <span className="font-mono text-xs text-slate-400">{item.event_id.slice(-8)}</span>
      </header>
      <p className="font-mono text-sm text-slate-700 break-words">{item.prompt_text}</p>
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="font-sans text-slate-400">Pair:</span>
        <span className={`px-2 py-0.5 rounded font-mono ${pairCls}`}>{pairText}</span>
        {(item.taxonomy_labels?.length ?? 0) > 0 && (
          <>
            <span className="font-sans text-slate-400">Taxonomy:</span>
            {item.taxonomy_labels!.map((label) => (
              <span
                key={label}
                className="px-2 py-0.5 rounded bg-blue-50 text-blue-600 font-mono"
              >
                {label}
              </span>
            ))}
          </>
        )}
      </div>
      <footer className="flex items-center gap-3 pt-3 border-t border-slate-200">
        {(['approve', 'dismiss', 'escalate'] as const).map((decision) => (
          <button
            key={decision}
            disabled={isPending}
            onClick={() => handleClick(decision)}
            className={BUTTON_STYLES[decision]}
            data-testid={`decide-${decision}`}
          >
            {isPending && activeDecision === decision ? (
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full border-2 border-current border-t-transparent animate-spin" />
                {decision}
              </span>
            ) : (
              decision.charAt(0).toUpperCase() + decision.slice(1)
            )}
          </button>
        ))}
      </footer>
    </article>
  )
}
