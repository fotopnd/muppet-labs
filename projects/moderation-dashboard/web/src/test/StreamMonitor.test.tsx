import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { StreamMonitor } from '@/pages/StreamMonitor'
import type { AnomalyFlag, StreamMetrics } from '@/types'

const STREAM_DATA: StreamMetrics = {
  event_rate_per_sec: 4.2,
  category_counts: { toxic: 12, insult: 7 },
  total_events: 1500,
}

const ANOMALY_DATA: AnomalyFlag[] = [
  {
    id: 'flag-1',
    window_start: '2026-06-03T10:00:00Z',
    window_end: '2026-06-03T10:05:00Z',
    signal_name: 'event_volume',
    z_score: 4.1,
    value: 120,
    baseline_mean: 60,
    baseline_std: 10,
    created_at: new Date().toISOString(),
  },
]

const server = setupServer(
  http.get('http://localhost:8002/metrics/stream', () => HttpResponse.json(STREAM_DATA)),
  http.get('http://localhost:8002/metrics/anomalies', () => HttpResponse.json(ANOMALY_DATA)),
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}

describe('StreamMonitor', () => {
  it('renders event rate from API', async () => {
    renderWithQuery(<StreamMonitor />)
    const rate = await screen.findByText('4.2/s')
    expect(rate).toBeInTheDocument()
  })

  it('renders total events', async () => {
    renderWithQuery(<StreamMonitor />)
    const total = await screen.findByText('1,500')
    expect(total).toBeInTheDocument()
  })

  it('renders anomaly feed items', async () => {
    renderWithQuery(<StreamMonitor />)
    const signal = await screen.findByText('event_volume')
    expect(signal).toBeInTheDocument()
  })

  it('renders empty anomaly message when none', async () => {
    server.use(
      http.get('http://localhost:8002/metrics/anomalies', () => HttpResponse.json([])),
    )
    renderWithQuery(<StreamMonitor />)
    const msg = await screen.findByText('No anomalies detected')
    expect(msg).toBeInTheDocument()
  })

  it('renders error state when stream API fails', async () => {
    server.use(
      http.get('http://localhost:8002/metrics/stream', () => HttpResponse.error()),
    )
    renderWithQuery(<StreamMonitor />)
    const error = await screen.findByText('Failed to load stream metrics')
    expect(error).toBeInTheDocument()
  })
})
