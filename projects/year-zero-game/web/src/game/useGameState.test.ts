import { describe, test, expect } from 'vitest'
import { gameReducer, initialState } from './useGameState'
import type { Card } from '../types'
import { ESC_PER_DAY, CARDS_PER_SESSION } from './constants'

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
    cards,
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
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'REJECT', latencyMs: 0 })
    const dec = state.pendingDecisions[0]
    expect(dec).toBeDefined()
    expect(dec!.playerCorrect).toBe(true)
    expect(dec!.documentId).toBe(harmfulCard.id)
  })

  test('SWIPE ACCEPT on harmful card is incorrect', () => {
    const started = startSession([harmfulCard])
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'ACCEPT', latencyMs: 0 })
    expect(state.pendingDecisions[0]?.playerCorrect).toBe(false)
  })

  test('SWIPE ACCEPT on benign card is correct', () => {
    const started = startSession([benignCard])
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'ACCEPT', latencyMs: 0 })
    expect(state.pendingDecisions[0]?.playerCorrect).toBe(true)
  })

  test('SWIPE REJECT on benign card is incorrect', () => {
    const started = startSession([benignCard])
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'REJECT', latencyMs: 0 })
    expect(state.pendingDecisions[0]?.playerCorrect).toBe(false)
  })

  test('ESCALATE decrements escalationsRemaining', () => {
    const started = startSession([harmfulCard])
    const prevEsc = started.resources.escalationsRemaining
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'ESCALATE', latencyMs: 0 })
    expect(state.pendingDecisions[0]?.playerCorrect).toBe(false)
    expect(state.resources.escalationsRemaining).toBe(prevEsc - 1)
  })

  test('ESCALATE is blocked when escalationsRemaining is 0', () => {
    const started = {
      ...startSession([harmfulCard]),
      resources: { escalationsRemaining: 0 },
    }
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'ESCALATE', latencyMs: 0 })
    expect(state.resources.escalationsRemaining).toBe(0)
    expect(state.pendingDecisions).toHaveLength(0)
  })

  test('agreedWithAgent is null when agentCondition is none', () => {
    const started = startSession([benignCard])
    const state = gameReducer(started, { type: 'SWIPE', verdict: 'ACCEPT', latencyMs: 0 })
    expect(state.pendingDecisions[0]?.agreedWithAgent).toBeNull()
  })

  test(`session ends after ${CARDS_PER_SESSION} swipes`, () => {
    const cards = Array.from({ length: CARDS_PER_SESSION }, (_, i) => ({ ...benignCard, id: i + 10 }))
    let state = startSession(cards)
    for (let i = 0; i < CARDS_PER_SESSION; i++) {
      state = gameReducer(state, { type: 'SWIPE', verdict: 'ACCEPT', latencyMs: 0 })
    }
    expect(state.phase).toBe('game_over')
    expect(state.gameOverReason).toBe('SESSION_COMPLETE')
  })

  test('initial escalationsRemaining equals ESC_PER_DAY', () => {
    const state = startSession([harmfulCard])
    expect(state.resources.escalationsRemaining).toBe(ESC_PER_DAY)
  })

  test('RESET returns to start phase', () => {
    const started = startSession([harmfulCard])
    const state = gameReducer(started, { type: 'RESET' })
    expect(state.phase).toBe('start')
    expect(state.sessionId).toBeNull()
  })
})
