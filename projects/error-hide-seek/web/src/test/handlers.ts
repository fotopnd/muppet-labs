import { http, HttpResponse } from 'msw'

import type { ExperimentResults, Session } from '@/types'

export const mockSession: Session = {
  session_id: 1,
  experiment_id: 1,
  paper_id: 1,
  paper_title: 'Alignment via Feedback: A Study on RLHF',
  condition: 'unaided',
  status: 'open',
  abstract_text:
    'We demonstrate that RLHF does not improve alignment by 30% on standard benchmarks. ' +
    'Our study covers 500 participants across five safety-relevant tasks.',
  annotations: [],
  scored_result: null,
}

export const mockSessionHumanAgent: Session = {
  ...mockSession,
  session_id: 2,
  condition: 'human_agent',
  annotations: [
    {
      id: 1,
      text_excerpt: 'does not improve alignment by 30%',
      confidence: 'high',
      reason: 'This claim contradicts established RLHF literature.',
    },
  ],
}

export const mockSessionCompleted: Session = {
  ...mockSession,
  session_id: 3,
  status: 'completed',
}

export const mockResults: ExperimentResults = {
  experiment_id: 1,
  uplift: 0.15,
  conditions: [
    {
      condition: 'unaided',
      sessions_total: 3,
      sessions_complete: 3,
      true_positive_rate: 0.33,
      false_positive_rate: 0.1,
      by_category: [{ category: 'inverted_conclusion', planted_count: 3, detected_count: 1, tpr: 0.33 }],
    },
    {
      condition: 'agent_only',
      sessions_total: 3,
      sessions_complete: 3,
      true_positive_rate: 0.67,
      false_positive_rate: 0.05,
      by_category: [{ category: 'inverted_conclusion', planted_count: 3, detected_count: 2, tpr: 0.67 }],
    },
    {
      condition: 'human_agent',
      sessions_total: 3,
      sessions_complete: 3,
      true_positive_rate: 0.48,
      false_positive_rate: 0.08,
      by_category: [{ category: 'inverted_conclusion', planted_count: 3, detected_count: 1, tpr: 0.33 }],
    },
  ],
}

export const mockResultsIncomplete: ExperimentResults = {
  experiment_id: 2,
  uplift: null,
  conditions: [
    {
      condition: 'unaided',
      sessions_total: 3,
      sessions_complete: 1,
      true_positive_rate: null,
      false_positive_rate: null,
      by_category: [],
    },
    {
      condition: 'agent_only',
      sessions_total: 3,
      sessions_complete: 0,
      true_positive_rate: null,
      false_positive_rate: null,
      by_category: [],
    },
    {
      condition: 'human_agent',
      sessions_total: 3,
      sessions_complete: 0,
      true_positive_rate: null,
      false_positive_rate: null,
      by_category: [],
    },
  ],
}

export const handlers = [
  http.get('http://localhost:8004/sessions/:id', ({ params }) => {
    const id = Number(params['id'])
    if (id === 2) return HttpResponse.json(mockSessionHumanAgent)
    if (id === 3) return HttpResponse.json(mockSessionCompleted)
    if (id === 999) return new HttpResponse(null, { status: 404 })
    return HttpResponse.json(mockSession)
  }),

  http.post('http://localhost:8004/reviews', () =>
    HttpResponse.json({ session_id: 1, status: 'completed' }, { status: 201 }),
  ),

  http.get('http://localhost:8004/results/:id', ({ params }) => {
    const id = Number(params['id'])
    if (id === 2) return HttpResponse.json(mockResultsIncomplete)
    return HttpResponse.json(mockResults)
  }),

  http.get('http://localhost:8004/experiments', () => HttpResponse.json([])),

  http.get('http://localhost:8004/papers', () =>
    HttpResponse.json({ items: [], total: 0, offset: 0, limit: 20 }),
  ),
]
