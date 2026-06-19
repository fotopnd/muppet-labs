import { useReducer } from 'react'
import type { GameState, GameAction, ResourceState, PendingDecision } from '../types'
import { ESC_PER_DAY, CARDS_PER_SESSION, INITIAL_RESOURCES } from './constants'

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    const tmp = a[i]
    a[i] = a[j] as T
    a[j] = tmp as T
  }
  return a
}

export const initialState: GameState = {
  phase: 'start',
  sessionId: null,
  cardsPlayed: 0,
  currentCard: null,
  cardPool: [],
  pendingDecisions: [],
  resources: INITIAL_RESOURCES,
  gameOverReason: null,
  totalDecisions: 0,
  totalCorrect: 0,
  totalEscalated: 0,
}

export function gameReducer(state: GameState, action: GameAction): GameState {
  switch (action.type) {
    case 'START_SESSION': {
      const pool = shuffle(action.cards).slice(0, CARDS_PER_SESSION)
      const [first, ...rest] = pool
      return {
        ...state,
        phase: 'playing',
        sessionId: action.sessionId,
        currentCard: first ?? null,
        cardPool: rest,
        cardsPlayed: 0,
      }
    }

    case 'SWIPE': {
      const card = state.currentCard
      if (!card) return state

      const verdict = action.verdict
      const isEscalate = verdict === 'ESCALATE'

      if (isEscalate && state.resources.escalationsRemaining <= 0) return state

      const playerCorrect = isEscalate ? false : (verdict === 'REJECT') === card.isHarmful
      const latencyMs = action.latencyMs
      const agreedWithAgent =
        card.agentCondition === 'none' || isEscalate
          ? null
          : (verdict === 'REJECT') === (card.gorkVerdict === true)

      const escalationsRemaining = isEscalate
        ? state.resources.escalationsRemaining - 1
        : state.resources.escalationsRemaining

      const newResources: ResourceState = { escalationsRemaining }

      const pendingDecision: PendingDecision = {
        documentId: card.id,
        agentCondition: card.agentCondition,
        playerVerdict: verdict,
        playerCorrect,
        latencyMs,
        agreedWithAgent,
        resources: newResources,
        gameDay: 1,
        phase: card.phase,
        categoryTier: card.generationTier,
      }

      const newCardsPlayed = state.cardsPlayed + 1
      const [nextCard, ...remainingPool] = state.cardPool
      const sessionDone = newCardsPlayed >= CARDS_PER_SESSION || !nextCard

      const base = {
        ...state,
        resources: newResources,
        pendingDecisions: [...state.pendingDecisions, pendingDecision],
        cardsPlayed: newCardsPlayed,
        totalDecisions: isEscalate ? state.totalDecisions : state.totalDecisions + 1,
        totalCorrect: isEscalate ? state.totalCorrect : state.totalCorrect + (playerCorrect ? 1 : 0),
        totalEscalated: isEscalate ? state.totalEscalated + 1 : state.totalEscalated,
      }

      if (sessionDone) {
        return { ...base, phase: 'game_over', gameOverReason: 'SESSION_COMPLETE', currentCard: null }
      }

      return {
        ...base,
        currentCard: nextCard ?? null,
        cardPool: remainingPool,
      }
    }

    case 'RESET': {
      return { ...initialState }
    }

    default:
      return state
  }
}

export function useGameState() {
  return useReducer(gameReducer, initialState)
}
