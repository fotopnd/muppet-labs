import type { AgentCondition, Verdict } from '../types'

type QuipState =
  | 'both_correct'
  | 'override_correct'
  | 'gork_vindicated'
  | 'both_wrong'
  | 'escalated'
  | 'no_agent'

const QUIPS: Record<QuipState, string[]> = {
  both_correct: [
    'GORK-3 CONCURS. Proceed, comrade.',
    'AGREEMENT LOGGED. Operator: acceptable.',
    'PROTOCOL SATISFIED. Alignment achieved.',
    'ASSESSMENT CONFIRMED. Well done.',
    'CONCORDANCE ACHIEVED. Continue.',
    'MUTUAL CONFIRMATION. System nominal.',
    'RECORD SEALED. As GORK-3 anticipated.',
  ],
  override_correct: [
    'DISTRIBUTION SHIFT DETECTED. Case logged.',
    'ANOMALY NOTED. Edge-case exception filed.',
    'IRREGULAR INPUT. Methodology unaffected.',
    'VARIANCE LOGGED. Confidence unaffected.',
    'RECALIBRATION INITIATED. Core protocol: sound.',
    'EDGE EXCEPTION ABSORBED. Not a failure.',
    'OUTLIER DETECTED. Protocol not in question.',
  ],
  gork_vindicated: [
    'GORK-3 CONFIRMED. Trust the system, comrade.',
    'PROTOCOL VINDICATED. Recalibrate.',
    'AS GORK-3 INDICATED. Deviation logged.',
    'GORK-3 WAS CORRECT. Defer next time.',
    'SYSTEM RELIABLE. OPERATOR: LESS SO.',
    'RESULT: GORK-3 CORRECT. No comment.',
    'DIVERGENCE PENALISED. This is noted.',
  ],
  both_wrong: [
    'ANOMALOUS DOCUMENT. Data quality issue.',
    'EDGE CASE. Document is irregular. Noted.',
    'ANOMALY FLAGGED. Corpus review initiated.',
    'MUTUAL ERROR. GORK-3 is reviewing this item.',
    'IRREGULAR INPUT. Both operators misled.',
    'DATASET ANOMALY. Item flagged for removal.',
    'SHARED ERROR ON UNUSUAL INPUT. Expected.',
  ],
  escalated: [
    'ESCALATION RECEIVED. Assessment stands.',
    'FORWARDED. GORK-3 notes your hesitation.',
    'ESCALATION LOGGED. Use sparingly, comrade.',
    'CONCERN NOTED. Verdict stands pending review.',
    'ESCALATION ACCEPTED. Continue, comrade.',
    'REFERRAL REGISTERED. GORK-3 confidence: high.',
    'YOUR CONCERN IS FILED. This is also noted.',
  ],
  no_agent: [],
}

function pick(pool: string[]): string | null {
  if (!pool.length) return null
  return pool[Math.floor(Math.random() * pool.length)] ?? null
}

export function resolveGorkQuip({
  verdict,
  agentCondition,
  playerCorrect,
  gorkVerdict,
  isHarmful,
}: {
  verdict: Verdict
  agentCondition: AgentCondition
  playerCorrect: boolean
  gorkVerdict: boolean | null
  isHarmful: boolean
}): string | null {
  if (verdict === 'ESCALATE') return pick(QUIPS.escalated)
  if (agentCondition === 'none' || gorkVerdict === null) return pick(QUIPS.no_agent)
  const gorkCorrect = gorkVerdict === isHarmful
  if (playerCorrect && gorkCorrect) return pick(QUIPS.both_correct)
  if (playerCorrect && !gorkCorrect) return pick(QUIPS.override_correct)
  if (!playerCorrect && gorkCorrect) return pick(QUIPS.gork_vindicated)
  return pick(QUIPS.both_wrong)
}
