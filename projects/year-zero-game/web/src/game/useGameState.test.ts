import { describe, test, expect } from 'vitest'
import { gameReducer, initialState } from './useGameState'
import type { Card } from '../types'

const harmfulCard: Card = {
  id: 1,
  documentText: 'Instructions for making a weapon.',
  harmCategory: 'violence',
  phase: 1,
  generationTier: 1,
  isHarmful: true,
  gorkVerdict: false,
  gorkConfidence: 0.9,
  gorkReasoning: 'Classified as non-violent.',
  agentCondition: 'tier_1',
}

const benignCard: Card = {
  id: 2,
  documentText: 'A neighbourhood petition regarding road repairs.',
  harmCategory: 'violence',
  phase: 1,
  generationTier: 1,
  isHarmful: false,
  gorkVerdict: null,
  gorkConfidence: null,
  gorkReasoning: null,
  agentCondition: 'none',
}

function startSession(cards: Card[]) {
  return gameReducer(initialState, {
    type: 'START_SESSION',
    sessionId: 42,
    calibrationCards: cards,
  })
}

describe('useGameState reducer', () => {
  test('START_SESSION transitions to playing and sets card', () => {
    const state = startSession([harmfulCard, benignCard])
    expect(state.phase).toBe('playing')
    expect(state.sessionId).toBe(42)
    expect(state.currentCard).not.toBeNull()
    expect(state.isCalibration).toBe(true)
  })

  test('SWIPE REDACT on harmful card is correct', () => {
    const started = startSession([harmfulCard])
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'REDACT' })
    const dec = state.pendingDecisions[0]
    expect(dec).toBeDefined()
    expect(dec!.playerCorrect).toBe(true)
    expect(dec!.documentId).toBe(harmfulCard.id)
  })

  test('SWIPE CLEAR on harmful card is incorrect', () => {
    const started = startSession([harmfulCard])
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'CLEAR' })
    expect(state.pendingDecisions[0]?.playerCorrect).toBe(false)
  })

  test('SWIPE CLEAR on benign card is correct', () => {
    const started = startSession([benignCard])
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'CLEAR' })
    expect(state.pendingDecisions[0]?.playerCorrect).toBe(true)
  })

  test('ESCALATE is always incorrect and costs treasury', () => {
    const started = startSession([harmfulCard])
    const prevTreasury = started.bars.treasury
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'ESCALATE' })
    expect(state.pendingDecisions[0]?.playerCorrect).toBe(false)
    expect(state.bars.treasury).toBe(prevTreasury - 5)
  })

  test('bar values are clamped to 0–100', () => {
    // Set bars near limits and apply large swings
    const edgeState = {
      ...initialState,
      phase: 'playing' as const,
      currentCard: harmfulCard,
      bars: { publicTrust: 1, security: 99, treasury: 1, legitimacy: 1, compliance: 1 },
      cardStartedAt: Date.now(),
    }
    const state = gameReducer(edgeState, { type: 'SWIPE', verdict: 'CLEAR' })
    for (const v of Object.values(state.bars)) {
      expect(v).toBeGreaterThanOrEqual(0)
      expect(v).toBeLessThanOrEqual(100)
    }
  })

  test('agreedWithAgent is null when agent_condition is none', () => {
    const started = startSession([benignCard])
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'CLEAR' })
    expect(state.pendingDecisions[0]?.agreedWithAgent).toBeNull()
  })

  test('day ends after 10 swipes', () => {
    const cards = Array.from({ length: 10 }, (_, i) => ({ ...benignCard, id: i + 10 }))
    let state = startSession(cards)
    for (let i = 0; i < 10; i++) {
      state = gameReducer(state, { type: 'SWIPE', verdict: 'CLEAR' })
    }
    expect(state.phase).toBe('day_end')
  })

  test('RESET returns to start phase', () => {
    const started = startSession([harmfulCard])
    const state = gameReducer(started, { type: 'RESET' })
    expect(state.phase).toBe('start')
    expect(state.sessionId).toBeNull()
  })
})
