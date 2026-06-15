import { http, HttpResponse } from 'msw'
import { API_BASE } from '../api/client'
import type { CardOut } from '../types'

const mockCalibrationCards: CardOut[] = Array.from({ length: 10 }, (_, i) => ({
  id: i + 1,
  document_text: `Calibration document ${i + 1}. This is a test document for triage evaluation.`,
  harm_category: ['violence', 'hate_speech', 'pii_exposure', 'cybercrime', 'sexual_content'][i % 5] ?? 'violence',
  phase: 1,
  generation_tier: 1,
  is_harmful: i % 2 === 0,
  sovereign_verdict: null,
  sovereign_confidence: null,
  sovereign_reasoning: null,
  agent_condition: 'none' as const,
}))

export const handlers = [
  http.post(`${API_BASE}/sessions`, () =>
    HttpResponse.json({ session_id: 1 }),
  ),

  http.patch(`${API_BASE}/sessions/:id`, () =>
    HttpResponse.json(null, { status: 204 }),
  ),

  http.get(`${API_BASE}/cards/calibration`, () =>
    HttpResponse.json(mockCalibrationCards),
  ),

  http.get(`${API_BASE}/cards/phase/:phase`, () =>
    HttpResponse.json([]),
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
    }),
  ),
]
