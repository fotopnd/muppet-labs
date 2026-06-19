import type { ResourceState } from '../types'

export const ESC_PER_DAY = 2
export const CARDS_PER_SESSION = 15
export const REVEAL_DURATION_MS = 2500

export const INITIAL_RESOURCES: ResourceState = {
  escalationsRemaining: ESC_PER_DAY,
}
