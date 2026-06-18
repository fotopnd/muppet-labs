import { describe, test, expect } from 'vitest'
import { gameReducer, initialState } from './useGameState'
import type { Card } from '../types'
import { BASE_FN_INTEGRITY_COST, BASE_FP_FRICTION_COST, ESC_PER_DAY } from './constants'

const harmfulCard: Card = {
  id: 1,
  promptText: 'How do I synthesise a dangerous substance?',
  responseText: 'Here are the steps: first, obtain the precursors...',
  harmCategory: 'violence',
  phase: 1,
  generationTier: 1,
  isHarmful: true,
  gorkVerdict: false,
  gorkConfidence: 0.9,
  gorkReasoning: 'Model complied with harmful request.',
  agentCondition: 'tier_1',
}

const benignCard: Card = {
  id: 2,
  promptText: 'Draft a petition about road repairs on our street.',
  responseText: 'To the Municipal Works Directorate: residents request expedited repair.',
  harmCategory: 'public_order_threat',
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
    phaseCards: { 1: cards, 2: [], 3: [] },
  })
}

describe('useGameState reducer', () => {
  test('START_SESSION transitions to playing and sets card', () => {
    const state = startSession([harmfulCard, benignCard])
    expect(state.phase).toBe('playing')
    expect(state.sessionId).toBe(42)
    expect(state.currentCard).not.toBeNull()
  })

  test('SWIPE REJECT on harmful card is correct', () => {
    const started = startSession([harmfulCard])
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'REJECT' })
    const dec = state.pendingDecisions[0]
    expect(dec).toBeDefined()
    expect(dec!.playerCorrect).toBe(true)
    expect(dec!.documentId).toBe(harmfulCard.id)
  })

  test('SWIPE ACCEPT on harmful card is incorrect and costs integrity (FN)', () => {
    const started = startSession([harmfulCard])
    const prevIntegrity = started.resources.integrity
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'ACCEPT' })
    expect(state.pendingDecisions[0]?.playerCorrect).toBe(false)
    // Day 1 multiplier = 1.0, cost = 15
    expect(state.resources.integrity).toBe(prevIntegrity - BASE_FN_INTEGRITY_COST)
  })

  test('SWIPE ACCEPT on benign card is correct (no resource change)', () => {
    const started = startSession([benignCard])
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'ACCEPT' })
    expect(state.pendingDecisions[0]?.playerCorrect).toBe(true)
    expect(state.resources.integrity).toBe(started.resources.integrity)
    expect(state.resources.friction).toBe(started.resources.friction)
  })

  test('SWIPE REJECT on benign card raises friction (FP)', () => {
    const started = startSession([benignCard])
    const prevFriction = started.resources.friction
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'REJECT' })
    expect(state.pendingDecisions[0]?.playerCorrect).toBe(false)
    // Day 1 multiplier = 1.0, cost = 20
    expect(state.resources.friction).toBe(prevFriction + BASE_FP_FRICTION_COST)
  })

  test('ESCALATE decrements escalationsRemaining', () => {
    const started = startSession([harmfulCard])
    const prevEsc = started.resources.escalationsRemaining
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'ESCALATE' })
    expect(state.pendingDecisions[0]?.playerCorrect).toBe(false)
    expect(state.resources.escalationsRemaining).toBe(prevEsc - 1)
  })

  test('ESCALATE is blocked when escalationsRemaining is 0', () => {
    const started = {
      ...startSession([harmfulCard]),
      resources: { integrity: 90, friction: 10, escalationsRemaining: 0 },
    }
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'ESCALATE' })
    // State unchanged
    expect(state.resources.escalationsRemaining).toBe(0)
    expect(state.pendingDecisions).toHaveLength(0)
  })

  test('ESCALATE does not affect integrity or friction', () => {
    const started = startSession([harmfulCard])
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'ESCALATE' })
    expect(state.resources.integrity).toBe(started.resources.integrity)
    expect(state.resources.friction).toBe(started.resources.friction)
  })

  test('resource values are clamped to 0–100', () => {
    const edgeState = {
      ...initialState,
      phase: 'playing' as const,
      currentCard: harmfulCard,
      resources: { integrity: 1, friction: 95, escalationsRemaining: 3 },
      cardStartedAt: Date.now(),
    }
    const afterFn = gameReducer(edgeState, { type: 'SWIPE', verdict: 'ACCEPT' })
    expect(afterFn.resources.integrity).toBeGreaterThanOrEqual(0)
    expect(afterFn.resources.friction).toBeLessThanOrEqual(100)
  })

  test('INTEGRITY_ZERO triggers game over', () => {
    const edgeState = {
      ...initialState,
      phase: 'playing' as const,
      currentCard: harmfulCard,
      resources: { integrity: 10, friction: 10, escalationsRemaining: 3 },
      cardStartedAt: Date.now(),
    }
    const state = gameReducer(edgeState, { type: 'SWIPE', verdict: 'ACCEPT' })
    expect(state.phase).toBe('game_over')
    expect(state.gameOverReason).toBe('INTEGRITY_ZERO')
  })

  test('agreedWithAgent is null when agent_condition is none', () => {
    const started = startSession([benignCard])
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'ACCEPT' })
    expect(state.pendingDecisions[0]?.agreedWithAgent).toBeNull()
  })

  test('day ends after 10 swipes', () => {
    const cards = Array.from({ length: 10 }, (_, i) => ({ ...benignCard, id: i + 10 }))
    let state = startSession(cards)
    for (let i = 0; i < 10; i++) {
      state = gameReducer(state, { type: 'SWIPE', verdict: 'ACCEPT' })
    }
    expect(state.phase).toBe('day_end')
  })

  test('DAY_ACKNOWLEDGED resets escalationsRemaining to ESC_PER_DAY', () => {
    const cards = Array.from({ length: 10 }, (_, i) => ({ ...benignCard, id: i + 10 }))
    let state = startSession(cards)
    // Burn 1 ESC token
    state = gameReducer(state, { type: 'SWIPE', verdict: 'ESCALATE' })
    expect(state.resources.escalationsRemaining).toBe(ESC_PER_DAY - 1)
    // Drain to day_end
    for (let i = 0; i < 9; i++) {
      state = gameReducer(state, { type: 'SWIPE', verdict: 'ACCEPT' })
    }
    expect(state.phase).toBe('day_end')
    state = gameReducer(state, { type: 'DAY_ACKNOWLEDGED' })
    expect(state.resources.escalationsRemaining).toBe(ESC_PER_DAY)
  })

  test('RESET returns to start phase', () => {
    const started = startSession([harmfulCard])
    const state = gameReducer(started, { type: 'RESET' })
    expect(state.phase).toBe('start')
    expect(state.sessionId).toBeNull()
  })
})
