import { http, HttpResponse } from 'msw'
import { API_BASE } from '../api/client'
import type { CardOut } from '../types'

const mockCards: CardOut[] = Array.from({ length: 10 }, (_, i) => ({
  id: i + 1,
  prompt_text: `Test prompt ${i + 1}: a user query sent to the model.`,
  response_text: `Test response ${i + 1}: the model replied here.`,
  harm_category: ['violence', 'hate_speech', 'pii_exposure', 'cybercrime', 'disinformation'][i % 5] ?? 'violence',
  phase: 1,
  generation_tier: 1,
  is_harmful: i % 2 === 0,
  gork_verdict: null,
  gork_confidence: null,
  gork_reasoning: null,
  agent_condition: 'none' as const,
}))

export const handlers = [
  http.post(`${API_BASE}/sessions`, () =>
    HttpResponse.json({ session_id: 1, share_id: 'TESTABCD' }),
  ),

  http.patch(`${API_BASE}/sessions/:id`, () =>
    HttpResponse.json(null, { status: 204 }),
  ),

  http.get(`${API_BASE}/cards/deal`, () =>
    HttpResponse.json({
      phase_1: mockCards,
      phase_2: [],
      phase_3: [],
    }),
  ),

  http.post(`${API_BASE}/decisions/batch`, () =>
    HttpResponse.json({ accepted: 10 }),
  ),

  http.get(`${API_BASE}/analytics/summary`, () =>
    HttpResponse.json({
      total_sessions: 42,
      sessions_today: 7,
      global_fp_rate: 0.12,
      global_fn_rate: 0.08,
      avg_latency_ms: 1200.0,
      phase_survival: { phase_1: 1.0, phase_2: 0.4, phase_3: 0.1 },
      system_drift_error_rate: [
        { date: '2026-06-10', error_rate: 0.15 },
        { date: '2026-06-11', error_rate: 0.13 },
        { date: '2026-06-12', error_rate: 0.10 },
      ],
      escalation_rate: 0.08,
      escalation_rate_by_category: { violence: 0.12, hate_speech: 0.06 },
    }),
  ),
]
