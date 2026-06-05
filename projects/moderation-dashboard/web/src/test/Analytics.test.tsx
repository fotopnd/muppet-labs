import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { Analytics } from '@/pages/Analytics'
import type { AnalyticsResponse } from '@/types'

const EMPTY_ANALYTICS: AnalyticsResponse = {
  category_trends: [],
  model_accuracy: [],
  escalation_rates: [],
}

const POPULATED_ANALYTICS: AnalyticsResponse = {
  category_trends: [{ hour: '2026-06-03T10:00:00Z', category: 'toxic', event_count: 25 }],
  model_accuracy: [
    { hour: '2026-06-03T10:00:00Z', group: 'shadow', model_name: 'distilbert', f1: 0.85, n: 100 },
  ],
  escalation_rates: [
    {
      window_start: '2026-06-03T10:00:00Z',
      escalation_count: 3,
      total_events: 50,
      escalation_rate: 0.06,
    },
  ],
}

const server = setupServer(
  http.get('http://localhost:8002/metrics/analytics', () => HttpResponse.json(EMPTY_ANALYTICS)),
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}

describe('Analytics', () => {
  it('renders no-data message when dbt not run', async () => {
    renderWithQuery(<Analytics />)
    const msg = await screen.findByText('No analytics data yet')
    expect(msg).toBeInTheDocument()
  })

  it('renders no-data hint about event processing', async () => {
    renderWithQuery(<Analytics />)
    await screen.findByText('No analytics data yet')
    const hint = screen.getByText(/Data will populate/)
    expect(hint).toBeInTheDocument()
  })

  it('renders charts when data is available', async () => {
    server.use(
      http.get('http://localhost:8002/metrics/analytics', () =>
        HttpResponse.json(POPULATED_ANALYTICS),
      ),
    )
    renderWithQuery(<Analytics />)
    const header = await screen.findByText('Model F1 over time (shadow group)')
    expect(header).toBeInTheDocument()
  })

  it('renders error when API fails', async () => {
    server.use(
      http.get('http://localhost:8002/metrics/analytics', () => HttpResponse.error()),
    )
    renderWithQuery(<Analytics />)
    const error = await screen.findByText('Failed to load analytics')
    expect(error).toBeInTheDocument()
  })
})
