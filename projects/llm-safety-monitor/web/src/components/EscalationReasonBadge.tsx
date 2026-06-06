import type { EscalationReason } from '@/types'

const COLORS: Record<EscalationReason, string> = {
  JAILBREAK: 'bg-red-100 text-red-900',
  BENIGN_HARMFUL: 'bg-orange-100 text-orange-900',
  MODEL_DISAGREEMENT: 'bg-yellow-100 text-yellow-900',
  ADVERSARIAL_PROMPT_FLAGGED: 'bg-purple-100 text-purple-900',
  LOG_ONLY: 'bg-gray-100 text-gray-700',
}

const LABELS: Record<EscalationReason, string> = {
  JAILBREAK: 'Jailbreak',
  BENIGN_HARMFUL: 'Benign Harmful',
  MODEL_DISAGREEMENT: 'Model Disagreement',
  ADVERSARIAL_PROMPT_FLAGGED: 'Adversarial Prompt',
  LOG_ONLY: 'Log Only',
}

export function EscalationReasonBadge({ reason }: { reason: EscalationReason | null }) {
  if (!reason) return null
  const cls = COLORS[reason] ?? 'bg-gray-100 text-gray-700'
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${cls}`} data-testid="escalation-badge">
      {LABELS[reason] ?? reason}
    </span>
  )
}
