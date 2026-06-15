import { useCallback, useEffect, useRef } from 'react'
import { useGameState } from '../game/useGameState'
import { useCreateSession, useCalibrationCards, usePhaseCards, useBatchDecisions, usePatchSession } from '../api/hooks'
import StatusBar from '../game/StatusBar'
import DocumentCard from '../game/DocumentCard'
import DayScreen from '../game/DayScreen'
import UpgradeScreen from '../game/UpgradeScreen'
import GameOver from '../game/GameOver'
import StartScreen from '../game/StartScreen'
import LorePage from '../game/LorePage'
import type { Verdict } from '../types'

export default function Game() {
  const [state, dispatch] = useGameState()
  const createSession = useCreateSession()
  const batchDecisions = useBatchDecisions()
  const patchSession = usePatchSession()

  // Set to true when user clicks "Begin Intake" — gates session creation
  const userReady = useRef(false)

  const handleBeginIntake = useCallback(() => {
    if (userReady.current) return
    userReady.current = true
    createSession.mutate(undefined)
  }, [createSession])

  const sessionId = createSession.data?.session_id ?? null

  // Fetch calibration cards when session is ready
  const { data: calibCards } = useCalibrationCards({ enabled: !!sessionId })

  // Start session when both session and calibration cards are ready
  const gameStarted = useRef(false)
  useEffect(() => {
    if (gameStarted.current) return
    if (!sessionId || !calibCards || state.phase !== 'start') return
    gameStarted.current = true
    dispatch({ type: 'START_SESSION', sessionId, calibrationCards: calibCards })
  }, [sessionId, calibCards, state.phase, dispatch])

  // Fetch phase cards when pool is empty and we're playing non-calibration
  const needsPhaseCards =
    !state.isCalibration &&
    state.cardPool.length === 0 &&
    state.currentCard === null &&
    state.phase === 'playing'

  const { data: phaseCards } = usePhaseCards(state.activePhase, {
    enabled: needsPhaseCards,
    categoryTiers: state.categoryTiers,
  })

  const phaseCardsDispatched = useRef<number | null>(null)
  useEffect(() => {
    if (!phaseCards || !needsPhaseCards) return
    if (phaseCardsDispatched.current === state.activePhase) return
    phaseCardsDispatched.current = state.activePhase
    dispatch({ type: 'PHASE_CARDS_LOADED', cards: phaseCards })
  }, [phaseCards, needsPhaseCards, state.activePhase, dispatch])

  // Batch submit when day ends
  const batchSubmitted = useRef<number | null>(null)
  useEffect(() => {
    if (state.phase !== 'day_end') return
    if (!sessionId) return
    if (batchSubmitted.current === state.gameDay) return
    batchSubmitted.current = state.gameDay
    batchDecisions.mutate({
      sessionId,
      gameDay: state.gameDay,
      decisions: state.pendingDecisions,
    })
  }, [state.phase, state.gameDay, sessionId, state.pendingDecisions, batchDecisions])

  // Patch session on game over
  const patchSubmitted = useRef(false)
  useEffect(() => {
    if (state.phase !== 'game_over') return
    if (!sessionId || patchSubmitted.current) return
    patchSubmitted.current = true
    const totalDecisions = state.totalDecisions
    const totalCorrect = state.totalCorrect
    const calibDecisions = state.pendingDecisions.filter((d) => d.isCalibration).length
    const calibCorrect = state.pendingDecisions.filter((d) => d.isCalibration && d.playerCorrect).length
    const agreements = state.pendingDecisions.filter((d) => d.agreedWithAgent === true).length
    const overrides = state.pendingDecisions.filter((d) => d.agreedWithAgent === false).length
    patchSession.mutate({
      sessionId,
      totalDays: state.gameDay,
      totalDecisions,
      correctDecisions: totalCorrect,
      accuracy: totalDecisions > 0 ? totalCorrect / totalDecisions : 0,
      phaseReached: state.activePhase,
      gameOverCondition: state.gameOverReason ?? 'UNKNOWN',
      finalBars: state.bars,
      categoryTiers: state.categoryTiers,
      calibrationAccuracy: calibDecisions > 0 ? calibCorrect / calibDecisions : 0,
      calibrationDecisions: calibDecisions,
      totalAgreements: agreements,
      totalOverrides: overrides,
    })
  }, [state.phase, sessionId]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleVerdictCommit = useCallback((verdict: Verdict) => {
    dispatch({ type: 'SWIPE', verdict })
  }, [dispatch])

  const handleDayContinue = useCallback(() => {
    dispatch({ type: 'DAY_ACKNOWLEDGED' })
  }, [dispatch])

  const handleUpgradeAck = useCallback(() => {
    if (state.upgradePending) {
      dispatch({ type: 'UPGRADE_ACKNOWLEDGED', category: state.upgradePending })
    }
  }, [dispatch, state.upgradePending])

  const handleReturn = useCallback(() => {
    userReady.current = false
    gameStarted.current = false
    patchSubmitted.current = false
    batchSubmitted.current = null
    phaseCardsDispatched.current = null
    createSession.reset()
    dispatch({ type: 'RESET' })
  }, [dispatch, createSession])

  const upgradeNewTier = state.upgradePending
    ? (Math.min(3, (state.categoryTiers[state.upgradePending] ?? 1) + 1) as 1 | 2 | 3)
    : 2

  const totalDecisions = state.totalDecisions
  const accuracy = totalDecisions > 0 ? state.totalCorrect / totalDecisions : 0

  return (
    <div className="w-full min-h-svh bg-pixel-room flex flex-col">
      {/* Overlays (highest z) */}
      {state.phase === 'start' && <StartScreen onStart={handleBeginIntake} loading={createSession.isPending} />}
      {state.phase === 'lore' && <LorePage onContinue={() => dispatch({ type: 'DAY_ACKNOWLEDGED' })} />}
      {state.phase === 'day_end' && (
        <DayScreen
          gameDay={state.gameDay}
          dayCorrect={state.dayCorrect}
          totalDecisions={totalDecisions}
          totalCorrect={state.totalCorrect}
          onContinue={handleDayContinue}
        />
      )}
      {state.phase === 'upgrade' && state.upgradePending && (
        <UpgradeScreen
          category={state.upgradePending}
          newTier={upgradeNewTier}
          onAcknowledge={handleUpgradeAck}
        />
      )}
      {state.phase === 'game_over' && state.gameOverReason && (
        <GameOver
          reason={state.gameOverReason}
          days={state.gameDay}
          decisions={totalDecisions}
          accuracy={accuracy}
          onReturn={handleReturn}
        />
      )}

      {/* Status bar */}
      <StatusBar bars={state.bars} />

      {/* Desk zone */}
      <div className="flex-1 flex flex-col items-center justify-center pt-12">
        <div
          className="w-full flex flex-col items-center justify-center py-12 rounded-sm"
          style={{
            background:
              'radial-gradient(ellipse at 50% 40%, var(--color-pixel-desk-lit) 0%, var(--color-pixel-desk) 70%)',
          }}
        >
          {state.phase === 'playing' && state.currentCard ? (
            <>
              <DocumentCard
                key={state.currentCard.id}
                card={state.currentCard}
                onVerdictCommit={handleVerdictCommit}
              />
              <div className="flex justify-between w-[80vw] max-w-[340px] mt-3">
                <span className="font-pixel text-pixel-room/60 text-[8px]">← REDACT</span>
                <span className="font-pixel text-pixel-room/60 text-[8px]">CLEAR →</span>
              </div>
            </>
          ) : state.phase === 'playing' && !state.currentCard ? (
            <p className="font-pixel text-pixel-terminal text-[8px]">LOADING...</p>
          ) : null}
        </div>
      </div>

      {/* Day counter */}
      {state.phase === 'playing' && (
        <div className="text-center pb-4">
          <span className="font-pixel text-pixel-card/40 text-[7px]">
            DAY {state.gameDay} — {state.cardsInDay}/10
          </span>
        </div>
      )}
    </div>
  )
}
