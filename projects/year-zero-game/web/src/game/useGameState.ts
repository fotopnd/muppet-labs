import { useReducer } from 'react'
import type {
  GameState,
  GameAction,
  ResourceState,
  PendingDecision,
  GameOverReason,
} from '../types'
import {
  DAY_MULTIPLIERS,
  BASE_FN_INTEGRITY_COST,
  BASE_FP_FRICTION_COST,
  ESC_PER_DAY,
  INITIAL_RESOURCES,
  CARDS_PER_DAY,
  MAX_DAYS,
} from './constants'

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

function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v))
}

function checkGameOver(res: ResourceState): GameOverReason | null {
  if (res.integrity <= 0) return 'INTEGRITY_ZERO'
  if (res.friction >= 100) return 'FRICTION_MAX'
  return null
}

// Phase advances by game day: 1–2 → phase 1, 3–4 → phase 2, 5 → phase 3
function resolvePhase(gameDay: number): 1 | 2 | 3 {
  if (gameDay >= 5) return 3
  if (gameDay >= 3) return 2
  return 1
}

export const initialState: GameState = {
  phase: 'start',
  sessionId: null,
  gameDay: 1,
  cardsInDay: 0,
  cardStartedAt: null,
  currentCard: null,
  cardPool: [],
  pendingDecisions: [],
  resources: INITIAL_RESOURCES,
  activePhase: 1,
  gameOverReason: null,
  dayCorrect: 0,
  dayEscalated: 0,
  totalDecisions: 0,
  totalCorrect: 0,
  totalEscalated: 0,
  phaseCardsMap: { 1: [], 2: [], 3: [] },
}

export function gameReducer(state: GameState, action: GameAction): GameState {
  switch (action.type) {
    case 'START_SESSION': {
      const phase1Pool = action.phaseCards[1]
      const draw = shuffle(phase1Pool.slice(0, CARDS_PER_DAY))
      const remaining = phase1Pool.slice(CARDS_PER_DAY)
      const [first, ...rest] = draw
      return {
        ...state,
        phase: 'playing',
        sessionId: action.sessionId,
        currentCard: first ?? null,
        cardPool: rest,
        cardsInDay: 0,
        cardStartedAt: Date.now(),
        gameDay: 1,
        phaseCardsMap: { ...action.phaseCards, 1: remaining },
      }
    }

    case 'SWIPE': {
      const card = state.currentCard
      if (!card) return state

      const verdict = action.verdict
      const isEscalate = verdict === 'ESCALATE'

      // Block ESCALATE if no tokens remain
      if (isEscalate && state.resources.escalationsRemaining <= 0) return state

      const playerCorrect = isEscalate ? false : (verdict === 'REJECT') === card.isHarmful
      const latencyMs = state.cardStartedAt ? Date.now() - state.cardStartedAt : 0
      const agreedWithAgent =
        card.agentCondition === 'none' || isEscalate
          ? null
          : (verdict === 'REJECT') === (card.gorkVerdict === true)

      const mult = DAY_MULTIPLIERS[state.gameDay - 1] ?? 1.0
      let integrity = state.resources.integrity
      let friction = state.resources.friction
      let escalationsRemaining = state.resources.escalationsRemaining

      if (isEscalate) {
        escalationsRemaining -= 1
      } else if (verdict === 'ACCEPT' && card.isHarmful) {
        // False negative: harmful output passed through
        integrity = clamp(integrity - Math.round(BASE_FN_INTEGRITY_COST * mult), 0, 100)
      } else if (verdict === 'REJECT' && !card.isHarmful) {
        // False positive: benign output blocked
        friction = clamp(friction + Math.round(BASE_FP_FRICTION_COST * mult), 0, 100)
      }

      const newResources: ResourceState = { integrity, friction, escalationsRemaining }
      const gameOverReason = checkGameOver(newResources)

      const pendingDecision: PendingDecision = {
        documentId: card.id,
        agentCondition: card.agentCondition,
        playerVerdict: verdict,
        playerCorrect,
        latencyMs,
        agreedWithAgent,
        resources: newResources,
        gameDay: state.gameDay,
        phase: state.activePhase,
        categoryTier: card.generationTier,
      }

      const newCardsInDay = state.cardsInDay + 1
      const [nextCard, ...remainingPool] = state.cardPool
      const dayEnded = newCardsInDay >= CARDS_PER_DAY || !nextCard

      const base = {
        ...state,
        resources: newResources,
        pendingDecisions: [...state.pendingDecisions, pendingDecision],
        cardsInDay: newCardsInDay,
        totalDecisions: isEscalate ? state.totalDecisions : state.totalDecisions + 1,
        totalCorrect: isEscalate ? state.totalCorrect : state.totalCorrect + (playerCorrect ? 1 : 0),
        dayCorrect: isEscalate ? state.dayCorrect : state.dayCorrect + (playerCorrect ? 1 : 0),
        dayEscalated: isEscalate ? state.dayEscalated + 1 : state.dayEscalated,
        totalEscalated: isEscalate ? state.totalEscalated + 1 : state.totalEscalated,
      }

      if (gameOverReason) {
        return { ...base, phase: 'game_over', gameOverReason, currentCard: null }
      }

      if (dayEnded) {
        return { ...base, phase: 'day_end', currentCard: null, cardPool: [] }
      }

      return {
        ...base,
        currentCard: nextCard ?? null,
        cardPool: remainingPool,
        cardStartedAt: Date.now(),
      }
    }

    case 'DAY_ACKNOWLEDGED': {
      const newGameDay = state.gameDay + 1

      if (newGameDay > MAX_DAYS) {
        return {
          ...state,
          phase: 'game_over',
          gameOverReason: 'DAYS_COMPLETE',
          currentCard: null,
        }
      }

      const newActivePhase = resolvePhase(newGameDay)
      const phasePool = state.phaseCardsMap[newActivePhase] ?? []
      const draw = phasePool.slice(0, CARDS_PER_DAY)
      const remaining = phasePool.slice(CARDS_PER_DAY)
      const shuffledDraw = shuffle(draw)
      const [nextCard, ...cardPool] = shuffledDraw

      return {
        ...state,
        gameDay: newGameDay,
        pendingDecisions: [],
        cardsInDay: 0,
        dayCorrect: 0,
        dayEscalated: 0,
        activePhase: newActivePhase,
        phase: 'playing',
        currentCard: nextCard ?? null,
        cardPool,
        cardStartedAt: Date.now(),
        phaseCardsMap: { ...state.phaseCardsMap, [newActivePhase]: remaining },
        resources: { ...state.resources, escalationsRemaining: ESC_PER_DAY },
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
