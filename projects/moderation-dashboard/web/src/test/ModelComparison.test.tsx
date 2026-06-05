import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { ModelComparison } from '@/pages/ModelComparison'
import type { ModelMetrics } from '@/types'

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
  },
]

const server = setupServer(
  http.get('http://localhost:8002/metrics/shadow', () => HttpResponse.json(SHADOW_DATA)),
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
})
