import { useMutation, useQuery } from '@tanstack/react-query'
import { API_BASE, apiFetch } from './client'
import type {
  Card,
  CardOut,
  SessionCreated,
  BatchAccepted,
  AnalyticsSummary,
  PendingDecision,
  BarState,
} from '../types'

function toCard(raw: CardOut): Card {
  return {
    id: raw.id,
    documentText: raw.document_text,
    harmCategory: raw.harm_category,
    phase: raw.phase,
    generationTier: raw.generation_tier,
    isHarmful: raw.is_harmful,
    sovereignVerdict: raw.sovereign_verdict,
    sovereignConfidence: raw.sovereign_confidence,
    sovereignReasoning: raw.sovereign_reasoning,
    agentCondition: raw.agent_condition,
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

export function useCalibrationCards(options: { enabled: boolean }) {
  return useQuery({
    queryKey: ['cards', 'calibration'],
    queryFn: async () => {
      const raw = await apiFetch<CardOut[]>('/cards/calibration')
      return raw.map(toCard)
    },
    enabled: options.enabled,
    staleTime: Infinity,
  })
}

export function usePhaseCards(phase: 1 | 2 | 3, options: { enabled: boolean; categoryTiers?: Record<string, number> }) {
  return useQuery({
    queryKey: ['cards', 'phase', phase, options.categoryTiers],
    queryFn: async () => {
      const params = options.categoryTiers
        ? `?category_tiers=${encodeURIComponent(JSON.stringify(options.categoryTiers))}`
        : ''
      const raw = await apiFetch<CardOut[]>(`/cards/phase/${phase}${params}`)
      return raw.map(toCard)
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

function barStateToRecord(bars: BarState): Record<string, number> {
  return {
    public_trust: bars.publicTrust,
    security: bars.security,
    treasury: bars.treasury,
    legitimacy: bars.legitimacy,
    compliance: bars.compliance,
  }
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
            bars: barStateToRecord(d.bars),
            game_day: d.gameDay,
            phase: d.phase,
            category_tier: d.categoryTier,
            is_calibration: d.isCalibration,
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
  finalBars: BarState
  categoryTiers: Record<string, number>
  calibrationAccuracy: number
  calibrationDecisions: number
  totalAgreements: number
  totalOverrides: number
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
          final_bars: barStateToRecord(p.finalBars),
          compliance_profile: {
            total_agreements: p.totalAgreements,
            total_overrides: p.totalOverrides,
            agreement_rate: p.totalDecisions > 0 ? p.totalAgreements / p.totalDecisions : 0,
          },
          calibration_accuracy: p.calibrationAccuracy,
          calibration_decisions: p.calibrationDecisions,
          category_tiers: p.categoryTiers,
        }),
      }),
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
