import { useCallback, useEffect, useRef } from 'react'
import { useGameState } from '../game/useGameState'
import { useCreateSession, useDealCards, useBatchDecisions, usePatchSession } from '../api/hooks'
import DocumentCard from '../game/DocumentCard'
import GameOver from '../game/GameOver'
import StartScreen from '../game/StartScreen'
import LorePage from '../game/LorePage'
import type { Card, Verdict } from '../types'
import { CARDS_PER_SESSION } from '../game/constants'

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    const tmp = a[i]; a[i] = a[j] as T; a[j] = tmp as T
  }
  return a
}

export default function Game() {
  const [state, dispatch] = useGameState()
  const createSession = useCreateSession()
  const batchDecisions = useBatchDecisions()
  const patchSession = usePatchSession()

  const userReady = useRef(false)

  const handleBeginIntake = useCallback(() => {
    if (userReady.current) return
    userReady.current = true
    createSession.mutate(undefined)
  }, [createSession])

  const sessionId = createSession.data?.session_id ?? null
  const shareId = createSession.data?.share_id ?? null

  const { data: deal } = useDealCards({ enabled: !!sessionId })

  const gameStarted = useRef(false)
  useEffect(() => {
    if (gameStarted.current) return
    if (!sessionId || !deal || state.phase !== 'start') return
    gameStarted.current = true
    const allCards: Card[] = shuffle([...deal.phase_1, ...deal.phase_2, ...deal.phase_3]).slice(0, CARDS_PER_SESSION)
    dispatch({ type: 'START_SESSION', sessionId, cards: allCards })
  }, [sessionId, deal, state.phase, dispatch])

  const batchSubmitted = useRef(false)
  useEffect(() => {
    if (state.phase !== 'game_over') return
    if (!sessionId || batchSubmitted.current) return
    batchSubmitted.current = true
    batchDecisions.mutate({
      sessionId,
      gameDay: 1,
      decisions: state.pendingDecisions,
    })
  }, [state.phase, sessionId, state.pendingDecisions, batchDecisions])

  const patchSubmitted = useRef(false)
  useEffect(() => {
    if (state.phase !== 'game_over') return
    if (!sessionId || patchSubmitted.current) return
    patchSubmitted.current = true
    const { totalDecisions, totalCorrect } = state
    const agreements = state.pendingDecisions.filter((d) => d.agreedWithAgent === true).length
    const overrides = state.pendingDecisions.filter((d) => d.agreedWithAgent === false).length
    patchSession.mutate({
      sessionId,
      totalDays: 1,
      totalDecisions,
      correctDecisions: totalCorrect,
      accuracy: totalDecisions > 0 ? totalCorrect / totalDecisions : 0,
      phaseReached: 1,
      gameOverCondition: 'SESSION_COMPLETE',
      finalResources: state.resources,
      calibrationAccuracy: 0,
      calibrationDecisions: 0,
      totalAgreements: agreements,
      totalOverrides: overrides,
      totalEscalated: state.totalEscalated,
    })
  }, [state.phase, sessionId]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleVerdictCommit = useCallback(
    (verdict: Verdict) => {
      dispatch({ type: 'SWIPE', verdict })
    },
    [dispatch],
  )

  const handleReturn = useCallback(() => {
    userReady.current = false
    gameStarted.current = false
    patchSubmitted.current = false
    batchSubmitted.current = false
    createSession.reset()
    dispatch({ type: 'RESET' })
  }, [dispatch, createSession])

  const totalDecisions = state.totalDecisions
  const accuracy = totalDecisions > 0 ? state.totalCorrect / totalDecisions : 0

  return (
    <div className="w-full min-h-svh bg-pixel-room flex flex-col">
      {state.phase === 'start' && (
        <StartScreen onStart={handleBeginIntake} loading={createSession.isPending} />
      )}
      {state.phase === 'lore' && (
        <LorePage onContinue={() => dispatch({ type: 'RESET' })} />
      )}
      {state.phase === 'game_over' && state.gameOverReason && (() => {
        const gorkDecisions = state.pendingDecisions.filter(d => d.agreedWithAgent !== null)
        const gorkCorrectCount = gorkDecisions.filter(d =>
          (d.agreedWithAgent === true && d.playerCorrect) ||
          (d.agreedWithAgent === false && !d.playerCorrect)
        ).length
        const gorkAccuracy = gorkDecisions.length > 0 ? gorkCorrectCount / gorkDecisions.length : 0
        const gorkCorrect  = gorkDecisions.filter(d => d.agreedWithAgent === false && d.playerCorrect).length
        const totalGorkShown = state.pendingDecisions.filter(d => d.agentCondition !== 'none').length
        return (
          <GameOver
            reason={state.gameOverReason!}
            days={1}
            decisions={totalDecisions}
            accuracy={accuracy}
            gorkAccuracy={gorkAccuracy}
            gorkCorrect={gorkCorrect}
            totalGorkShown={totalGorkShown}
            shareId={shareId}
            onReturn={handleReturn}
          />
        )
      })()}

      <div className="flex-1 flex flex-col items-center justify-center">
        <div
          className="w-full flex flex-col items-center justify-center py-8 min-h-[480px]"
          style={{
            background:
              'radial-gradient(ellipse at 50% 40%, var(--color-pixel-desk-lit) 0%, var(--color-pixel-desk) 70%)',
          }}
        >
          {state.phase === 'playing' && state.currentCard ? (
            <DocumentCard
              key={state.currentCard.id}
              card={state.currentCard}
              escalationsRemaining={state.resources.escalationsRemaining}
              onVerdictCommit={handleVerdictCommit}
            />
          ) : state.phase === 'playing' && !state.currentCard ? (
            <p className="font-pixel text-pixel-terminal text-[8px]">LOADING...</p>
          ) : null}
        </div>
      </div>

      {state.phase === 'playing' && (
        <div className="flex justify-between px-6 py-3 w-full max-w-[360px] mx-auto">
          <span className="font-pixel text-pixel-card/40 text-[7px]">
            {state.cardsPlayed} / {CARDS_PER_SESSION} reviewed
          </span>
          <span className="font-pixel text-pixel-card/40 text-[7px]">
            {state.resources.escalationsRemaining} escalations
          </span>
        </div>
      )}
    </div>
  )
}
