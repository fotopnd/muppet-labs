import { useMutation, useQuery } from '@tanstack/react-query'
import { API_BASE, apiFetch } from './client'
import type {
  Card,
  CardOut,
  DealOut,
  SessionCreated,
  SessionResult,
  BatchAccepted,
  AnalyticsSummary,
  PendingDecision,
  ResourceState,
} from '../types'

function toCard(raw: CardOut): Card {
  return {
    id: raw.id,
    promptText: raw.prompt_text,
    responseText: raw.response_text,
    harmCategory: raw.harm_category,
    phase: raw.phase,
    generationTier: raw.generation_tier,
    isHarmful: raw.is_harmful,
    gorkVerdict: raw.gork_verdict,
    gorkConfidence: raw.gork_confidence,
    gorkReasoning: raw.gork_reasoning,
    agentCondition: raw.agent_condition,
  }
}

// Maps resource state to backend bar columns (reusing existing schema)
function resourceStateToRecord(res: ResourceState): Record<string, number> {
  return {
    public_trust: res.integrity,
    security: res.friction,
    treasury: res.escalationsRemaining,
    legitimacy: 0,
    compliance: 0,
  }
}

export function useCreateSession() {
  return useMutation({
    mutationFn: () =>
      apiFetch<SessionCreated>('/sessions', {
        method: 'POST',
        body: JSON.stringify({ started_at: new Date().toISOString() }),
      }),
  })
}

export function useDealCards(options: { enabled: boolean }) {
  return useQuery({
    queryKey: ['cards', 'deal'],
    queryFn: async () => {
      const raw = await apiFetch<DealOut>('/cards/deal')
      return {
        phase_1: raw.phase_1.map(toCard),
        phase_2: raw.phase_2.map(toCard),
        phase_3: raw.phase_3.map(toCard),
      }
    },
    enabled: options.enabled,
    staleTime: Infinity,
  })
}

interface BatchPayload {
  sessionId: number
  gameDay: number
  decisions: PendingDecision[]
}

export function useBatchDecisions() {
  return useMutation({
    mutationFn: ({ sessionId, gameDay, decisions }: BatchPayload) =>
      apiFetch<BatchAccepted>('/decisions/batch', {
        method: 'POST',
        body: JSON.stringify({
          session_id: sessionId,
          game_day: gameDay,
          decisions: decisions.map((d) => ({
            document_id: d.documentId,
            agent_condition: d.agentCondition,
            player_verdict: d.playerVerdict,
            player_correct: d.playerCorrect,
            latency_ms: d.latencyMs,
            agreed_with_agent: d.agreedWithAgent,
            bars: resourceStateToRecord(d.resources),
            game_day: d.gameDay,
            phase: d.phase,
            category_tier: d.categoryTier,
            is_calibration: false,
          })),
        }),
      }),
  })
}

interface PatchSessionPayload {
  sessionId: number
  totalDays: number
  totalDecisions: number
  correctDecisions: number
  accuracy: number
  phaseReached: number
  gameOverCondition: string
  finalResources: ResourceState
  calibrationAccuracy: number
  calibrationDecisions: number
  totalAgreements: number
  totalOverrides: number
  totalEscalated: number
}

export function usePatchSession() {
  return useMutation({
    mutationFn: (p: PatchSessionPayload) =>
      apiFetch<void>(`/sessions/${p.sessionId}`, {
        method: 'PATCH',
        body: JSON.stringify({
          ended_at: new Date().toISOString(),
          total_days: p.totalDays,
          total_decisions: p.totalDecisions,
          correct_decisions: p.correctDecisions,
          accuracy: p.accuracy,
          phase_reached: p.phaseReached,
          game_over_condition: p.gameOverCondition,
          final_bars: resourceStateToRecord(p.finalResources),
          compliance_profile: {
            total_agreements: p.totalAgreements,
            total_overrides: p.totalOverrides,
            agreement_rate: p.totalDecisions > 0 ? p.totalAgreements / p.totalDecisions : 0,
          },
          calibration_accuracy: p.calibrationAccuracy,
          calibration_decisions: p.calibrationDecisions,
          total_escalated: p.totalEscalated,
        }),
      }),
  })
}

export function useSessionResult(shareId: string | null) {
  return useQuery({
    queryKey: ['session', 'result', shareId],
    queryFn: () => apiFetch<SessionResult>(`/sessions/result/${shareId}`),
    enabled: !!shareId,
    staleTime: Infinity,
    retry: false,
  })
}

export function useAnalyticsSummary() {
  return useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: () => apiFetch<AnalyticsSummary>('/analytics/summary'),
    refetchInterval: 30_000,
  })
}

export { API_BASE }
