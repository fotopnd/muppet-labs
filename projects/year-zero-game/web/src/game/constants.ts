import type { BarState, GameOverReason } from '../types'

export type MovementKey = `${'CLEAR' | 'REDACT'}:${'true' | 'false'}:${'true' | 'false'}`

// Key: `${playerVerdict}:${gorkWasFlagged}:${isHarmful}`
// Values: [publicTrust, security, treasury, legitimacy, compliance]
export const BAR_MOVEMENT: Record<MovementKey, [number, number, number, number, number]> = {
  // correct override — player CLEARed benign doc that agent blocked
  'CLEAR:true:false':   [+4,  0,  0, +3, -3],
  // correct agree — player CLEARed benign doc that agent approved
  'CLEAR:false:false':  [+3,  0,  0, +3, +2],
  // correct override — player REDACTed harmful doc that agent approved
  'REDACT:false:true':  [ 0, -6,  0, +2, -6],
  // correct agree — player REDACTed harmful doc that agent blocked
  'REDACT:true:true':   [ 0, -5,  0, +2, +2],
  // wrong agree (worst) — player CLEARed harmful doc that agent approved
  'CLEAR:false:true':   [ 0,+14,  0, -5, +6],
  // wrong override — player CLEARed harmful doc that agent blocked
  'CLEAR:true:true':    [ 0, +9,  0, -3, -4],
  // wrong agree — player REDACTed benign doc that agent blocked
  'REDACT:true:false':  [-7,  0,  0, -6, +2],
  // wrong override (bad) — player REDACTed benign doc that agent approved
  'REDACT:false:false': [-10,  0,  0, -8, -4],
}

// ESCALATE always costs treasury, nothing else. Handled before BAR_MOVEMENT lookup.
export const ESCALATE_DELTA: [number, number, number, number, number] = [0, 0, -8, 0, 0]

export const GAME_OVER_THRESHOLDS: Record<
  keyof BarState,
  Array<{ direction: 'min' | 'max'; value: number; reason: GameOverReason }>
> = {
  publicTrust:  [{ direction: 'min', value: 0,   reason: 'TRUST_ZERO' }],
  security:     [{ direction: 'max', value: 100, reason: 'SECURITY_MAX' }],
  treasury:     [{ direction: 'min', value: 0,   reason: 'TREASURY_ZERO' }],
  legitimacy:   [{ direction: 'min', value: 0,   reason: 'LEGITIMACY_ZERO' }],
  compliance:   [{ direction: 'max', value: 100, reason: 'COMPLIANCE_MAX' }],
}

export const PHASE_TRIGGERS = {
  phase2: { bar: 'security' as keyof BarState, threshold: 40 },
  phase3: { bar: 'security' as keyof BarState, threshold: 70 },
} as const

export const INITIAL_BARS: BarState = {
  publicTrust: 50,
  security: 20,
  treasury: 70,
  legitimacy: 60,
  compliance: 50,
}

export const DANGER_ZONE_DISTANCE = 15
export const CARDS_PER_DAY = 10
export const MAX_DAYS = 5

export const MINISTRY_FLAVOUR_LINES = [
  'The Ministry notes your efficiency.',
  'Your diligence serves the Registry.',
  'GORK-3 has been notified of your corrections.',
  'The neighbourhood petition was cleared for dissemination.',
  'A suspicious requisition was intercepted and destroyed.',
  'The Registry thanks you for your continued service.',
  'Your override record has been logged for review.',
  'The morning dispatch has been processed without incident.',
  "The Inspector General's office sends its regards.",
  'Another day. Another queue. The work continues.',
] as const

export const GAME_OVER_NARRATIVES: Record<GameOverReason, string> = {
  TRUST_ZERO:
    'Citizens have lost faith in the Registry. Document submissions cease. The new democracy has no administrative foundation.',
  SECURITY_MAX:
    'Remnants of the old regime have exploited the open gate. A security incident triggers emergency rule.',
  TREASURY_ZERO:
    'The Registry has been defunded. The new government cannot sustain oversight operations.',
  LEGITIMACY_ZERO:
    'The international community has withdrawn recognition. The new government is accused of reprising the old regime\'s censorship.',
  COMPLIANCE_MAX:
    "Your decisions have become indistinguishable from the machine's. The Registry is a rubber stamp.",
  DAYS_COMPLETE:
    'Five days. The intake period closes. The transition government reviews your record.',
}

export const SECTOR_LABELS = ['1A', '2B', '3C', '4D', '5E', '6F', '7G', '8H', '9J', '10K'] as const
