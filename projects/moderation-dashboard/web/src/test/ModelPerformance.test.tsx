import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { ModelPerformance } from '@/pages/ModelPerformance'
import type { ModelMetrics } from '@/types'

const PRODUCTION_DATA: ModelMetrics[] = [
  {
    model_name: 'distilbert',
    display_name: 'DistilBERT (zero-shot)',
    status: 'active',
    event_count: 500,
    f1: 0.847,
    precision: 0.821,
    recall: 0.875,
    latency_p50: 45.2,
    latency_p95: 120.5,
    throughput_per_sec: 3.1,
    source: 'live',
    has_seeded_data: false,
    live_event_count: 500,
    live_flagged_count: 193,
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

const server = setupServer(
  http.get('http://localhost:8002/metrics/production', () => HttpResponse.json(PRODUCTION_DATA)),
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}

describe('ModelPerformance', () => {
  it('renders model cards with data', async () => {
    renderWithQuery(<ModelPerformance />)
    const name = await screen.findByText('DistilBERT (zero-shot)')
    expect(name).toBeInTheDocument()
  })

  it('shows LIVE badge for active models', async () => {
    renderWithQuery(<ModelPerformance />)
    const badge = await screen.findByText('LIVE')
    expect(badge).toBeInTheDocument()
  })

  it('shows Pending weights badge for pending_weights models', async () => {
    renderWithQuery(<ModelPerformance />)
    const badge = await screen.findByText('Pending weights')
    expect(badge).toBeInTheDocument()
  })

  it('shows awaiting checkpoint for pending model', async () => {
    renderWithQuery(<ModelPerformance />)
    const msg = await screen.findByText('Awaiting checkpoint')
    expect(msg).toBeInTheDocument()
  })

  it('renders error when API fails', async () => {
    server.use(
      http.get('http://localhost:8002/metrics/production', () => HttpResponse.error()),
    )
    renderWithQuery(<ModelPerformance />)
    const error = await screen.findByText('Failed to load production metrics')
    expect(error).toBeInTheDocument()
  })
})
