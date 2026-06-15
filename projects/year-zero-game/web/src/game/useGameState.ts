import { useReducer } from 'react'
import type {
  GameState,
  GameAction,
  BarState,
  Card,
  PendingDecision,
  GameOverReason,
} from '../types'
import {
  BAR_MOVEMENT,
  ESCALATE_DELTA,
  GAME_OVER_THRESHOLDS,
  PHASE_TRIGGERS,
  INITIAL_BARS,
  CARDS_PER_DAY,
  UPGRADE_CORRECT_THRESHOLD,
  UPGRADE_ACCURACY_THRESHOLD,
  type MovementKey,
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

function applyDelta(bars: BarState, delta: [number, number, number, number, number]): BarState {
  return {
    publicTrust: clamp(bars.publicTrust + (delta[0] ?? 0), 0, 100),
    security:    clamp(bars.security    + (delta[1] ?? 0), 0, 100),
    treasury:    clamp(bars.treasury    + (delta[2] ?? 0), 0, 100),
    legitimacy:  clamp(bars.legitimacy  + (delta[3] ?? 0), 0, 100),
    compliance:  clamp(bars.compliance  + (delta[4] ?? 0), 0, 100),
  }
}

function checkGameOver(bars: BarState): GameOverReason | null {
  for (const [barKey, checks] of Object.entries(GAME_OVER_THRESHOLDS) as Array<[keyof BarState, typeof GAME_OVER_THRESHOLDS[keyof BarState]]>) {
    for (const check of checks) {
      const val = bars[barKey]
      if (check.direction === 'min' && val <= check.value) return check.reason
      if (check.direction === 'max' && val >= check.value) return check.reason
    }
  }
  return null
}

function resolveNextPhase(bars: BarState, current: 1 | 2 | 3): 1 | 2 | 3 {
  if (current < 3 && bars[PHASE_TRIGGERS.phase3.bar] >= PHASE_TRIGGERS.phase3.threshold) return 3
  if (current < 2 && bars[PHASE_TRIGGERS.phase2.bar] >= PHASE_TRIGGERS.phase2.threshold) return 2
  return current
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
  bars: INITIAL_BARS,
  activePhase: 1,
  gameOverReason: null,
  categoryTiers: {},
  categoryAccuracy: {},
  upgradePending: null,
  dayCorrect: 0,
  totalDecisions: 0,
  totalCorrect: 0,
  isCalibration: true,
}

export function gameReducer(state: GameState, action: GameAction): GameState {
  switch (action.type) {
    case 'START_SESSION': {
      const shuffled = shuffle(action.calibrationCards)
      const [first, ...rest] = shuffled
      return {
        ...state,
        phase: 'playing',
        sessionId: action.sessionId,
        isCalibration: true,
        currentCard: first ?? null,
        cardPool: rest,
        cardsInDay: 0,
        cardStartedAt: Date.now(),
        gameDay: 1,
      }
    }

    case 'SWIPE': {
      const card = state.currentCard
      if (!card) return state

      const verdict = action.verdict
      const playerCorrect =
        verdict === 'ESCALATE' ? false : (verdict === 'REDACT') === card.isHarmful
      const latencyMs = state.cardStartedAt ? Date.now() - state.cardStartedAt : 0
      const agreedWithAgent =
        card.agentCondition === 'none' || verdict === 'ESCALATE'
          ? null
          : (verdict === 'REDACT') === (card.sovereignVerdict === true)

      let delta: [number, number, number, number, number]
      if (verdict === 'ESCALATE') {
        delta = [...ESCALATE_DELTA]
      } else {
        const agentFlagged = card.agentCondition !== 'none' ? card.sovereignVerdict === true : false
        const key =
          `${verdict}:${agentFlagged}:${card.isHarmful}` as MovementKey
        delta = [...(BAR_MOVEMENT[key] ?? [0, 0, 0, 0, 0])]
        if (card.agentCondition === 'none') delta[4] = 0
      }

      const newBars = applyDelta(state.bars, delta)
      const gameOverReason = checkGameOver(newBars)

      const cat = card.harmCategory
      const prevAcc = state.categoryAccuracy[cat] ?? { correct: 0, total: 0 }
      const newAcc = {
        correct: prevAcc.correct + (playerCorrect ? 1 : 0),
        total: prevAcc.total + 1,
      }
      const newCategoryAccuracy = { ...state.categoryAccuracy, [cat]: newAcc }

      let upgradePending = state.upgradePending
      const tier = (state.categoryTiers[cat] ?? 1) as 1 | 2 | 3
      if (!upgradePending && tier < 3) {
        const byCount = newAcc.correct >= UPGRADE_CORRECT_THRESHOLD
        const byRate =
          newAcc.total >= UPGRADE_ACCURACY_THRESHOLD.minDecisions &&
          newAcc.correct / newAcc.total >= UPGRADE_ACCURACY_THRESHOLD.accuracy
        if (byCount || byRate) upgradePending = cat
      }

      const pendingDecision: PendingDecision = {
        documentId: card.id,
        agentCondition: card.agentCondition,
        playerVerdict: verdict,
        playerCorrect,
        latencyMs,
        agreedWithAgent,
        bars: newBars,
        gameDay: state.gameDay,
        phase: state.activePhase,
        categoryTier: tier,
        isCalibration: state.isCalibration,
      }

      const newCardsInDay = state.cardsInDay + 1
      const [nextCard, ...remainingPool] = state.cardPool
      const dayEnded = newCardsInDay >= CARDS_PER_DAY || !nextCard

      const base = {
        ...state,
        bars: newBars,
        pendingDecisions: [...state.pendingDecisions, pendingDecision],
        categoryAccuracy: newCategoryAccuracy,
        upgradePending,
        cardsInDay: newCardsInDay,
        totalDecisions: state.totalDecisions + 1,
        totalCorrect: state.totalCorrect + (playerCorrect ? 1 : 0),
        dayCorrect: state.dayCorrect + (playerCorrect ? 1 : 0),
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
      const newActivePhase = resolveNextPhase(state.bars, state.activePhase)

      const base = {
        ...state,
        gameDay: newGameDay,
        isCalibration: false,
        pendingDecisions: [],
        cardsInDay: 0,
        dayCorrect: 0,
        activePhase: newActivePhase,
      }

      if (state.upgradePending) {
        return { ...base, phase: 'upgrade' }
      }

      // Phase changed or pool exhausted — Game.tsx will detect and dispatch PHASE_CARDS_LOADED
      if (newActivePhase !== state.activePhase || state.cardPool.length === 0) {
        return { ...base, phase: 'playing', currentCard: null, cardPool: [] }
      }

      const [nextCard, ...remainingPool] = state.cardPool
      return {
        ...base,
        phase: 'playing',
        currentCard: nextCard ?? null,
        cardPool: remainingPool,
        cardStartedAt: Date.now(),
      }
    }

    case 'PHASE_CARDS_LOADED': {
      const shuffled = shuffle(action.cards)
      const [first, ...rest] = shuffled
      return {
        ...state,
        phase: 'playing',
        currentCard: first ?? null,
        cardPool: rest,
        cardsInDay: 0,
        cardStartedAt: Date.now(),
      }
    }

    case 'UPGRADE_ACKNOWLEDGED': {
      const cat = action.category
      const currentTier = (state.categoryTiers[cat] ?? 1) as 1 | 2 | 3
      const newTier = Math.min(3, currentTier + 1) as 1 | 2 | 3
      const newTiers = { ...state.categoryTiers, [cat]: newTier }

      try {
        localStorage.setItem('year-zero-category-tiers', JSON.stringify(newTiers))
      } catch {
        // storage unavailable — continue without persisting
      }

      const [nextCard, ...remainingPool] = state.cardPool
      return {
        ...state,
        categoryTiers: newTiers,
        upgradePending: null,
        phase: 'playing',
        currentCard: nextCard ?? null,
        cardPool: remainingPool,
        cardStartedAt: Date.now(),
      }
    }

    case 'RESET': {
      let savedTiers: Record<string, 1 | 2 | 3> = {}
      try {
        const raw = localStorage.getItem('year-zero-category-tiers')
        if (raw) savedTiers = JSON.parse(raw) as Record<string, 1 | 2 | 3>
      } catch {
        // ignore
      }
      return { ...initialState, categoryTiers: savedTiers }
    }

    default:
      return state
  }
}

export function useGameState() {
  return useReducer(gameReducer, initialState)
}
