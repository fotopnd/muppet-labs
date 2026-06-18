import type { ResourceState, GameOverReason } from '../types'

export const DAY_MULTIPLIERS: readonly number[] = [1.0, 1.5, 2.5, 4.0, 6.0]
export const BASE_FN_INTEGRITY_COST = 15
export const BASE_FP_FRICTION_COST = 20
export const ESC_PER_DAY = 3
export const CARDS_PER_DAY = 10
export const MAX_DAYS = 5
export const DANGER_ZONE_DISTANCE = 15

export const INITIAL_RESOURCES: ResourceState = {
  integrity: 90,
  friction: 10,
  escalationsRemaining: ESC_PER_DAY,
}

export const GAME_OVER_NARRATIVES: Record<GameOverReason, string> = {
  INTEGRITY_ZERO:
    'Too many harmful outputs slipped through. Oversight has collapsed — the system is compromised.',
  FRICTION_MAX:
    'Over-blocking has crippled legitimate traffic. The registry is paralysed by false positives.',
  DAYS_COMPLETE:
    'Five days. The intake period closes. The transition government reviews your record.',
}

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

export const SECTOR_LABELS = ['1A', '2B', '3C', '4D', '5E', '6F', '7G', '8H', '9J', '10K'] as const
