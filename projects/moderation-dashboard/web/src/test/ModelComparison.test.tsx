import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { ModelComparison } from '@/pages/ModelComparison'
import type { DisagreementsResponse, ModelMetrics } from '@/types'

const SHADOW_DATA: ModelMetrics[] = [
  {
    model_name: 'distilbert',
    display_name: 'DistilBERT (zero-shot)',
    status: 'active',
    event_count: 200,
    f1: 0.889,
    precision: 0.9,
    recall: 0.879,
    latency_p50: 50.1,
    latency_p95: 130.2,
    throughput_per_sec: 2.8,
    source: 'live',
    has_seeded_data: false,
    live_event_count: 16092,
    live_flagged_count: 6208,
  },
  {
    model_name: 'finetuned_distilbert',
    display_name: 'DistilBERT (fine-tuned)',
    status: 'pending_weights',
    event_count: 0,
    f1: null,
    precision: null,
    recall: null,
    latency_p50: null,
    latency_p95: null,
    throughput_per_sec: null,
    source: 'seeded',
    has_seeded_data: false,
    live_event_count: 0,
    live_flagged_count: 0,
  },
]

const DISAGREEMENTS_DATA: DisagreementsResponse = {
  total_last_hour: 274,
  by_category: { clean: 180, toxic: 60, insult: 34 },
  samples: [
    {
      event_id: 'evt-1',
      content: 'Sample post text',
      verdicts: [
        { model_name: 'distilbert', predicted_label: 1, confidence: 0.71 },
        { model_name: 'detoxify', predicted_label: 0, confidence: 0.62 },
      ],
    },
  ],
}

const server = setupServer(
  http.get('http://localhost:8002/metrics/shadow', () => HttpResponse.json(SHADOW_DATA)),
  http.get('http://localhost:8002/metrics/disagreements', () =>
    HttpResponse.json(DISAGREEMENTS_DATA),
  ),
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}

describe('ModelComparison', () => {
  it('renders model cards with data', async () => {
    renderWithQuery(<ModelComparison />)
    const name = await screen.findByText('DistilBERT (zero-shot)')
    expect(name).toBeInTheDocument()
  })

  it('shows LIVE badge for active models', async () => {
    renderWithQuery(<ModelComparison />)
    const badge = await screen.findByText('LIVE')
    expect(badge).toBeInTheDocument()
  })

  it('shows Pending weights badge for pending_weights models', async () => {
    renderWithQuery(<ModelComparison />)
    const badge = await screen.findByText('Pending weights')
    expect(badge).toBeInTheDocument()
  })

  it('shows awaiting checkpoint for pending model', async () => {
    renderWithQuery(<ModelComparison />)
    const msg = await screen.findByText('Awaiting checkpoint')
    expect(msg).toBeInTheDocument()
  })

  it('renders error when API fails', async () => {
    server.use(
      http.get('http://localhost:8002/metrics/shadow', () => HttpResponse.error()),
    )
    renderWithQuery(<ModelComparison />)
    const error = await screen.findByText('Failed to load shadow metrics')
    expect(error).toBeInTheDocument()
  })

  it('shows live flag rate on active model card', async () => {
    renderWithQuery(<ModelComparison />)
    // distilbert: 6208/16092 = 38.6%
    const rate = await screen.findByText('38.6%')
    expect(rate).toBeInTheDocument()
  })

  it('shows disagreement panel with total count', async () => {
    renderWithQuery(<ModelComparison />)
    const total = await screen.findByText('274')
    expect(total).toBeInTheDocument()
  })

  it('shows disagreement sample post content', async () => {
    renderWithQuery(<ModelComparison />)
    const content = await screen.findByText('Sample post text')
    expect(content).toBeInTheDocument()
  })
})
