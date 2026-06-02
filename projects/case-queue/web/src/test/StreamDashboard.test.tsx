import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { StreamDashboard } from '@/pages/StreamDashboard'
import type { MetricsResponse } from '@/types/stream'

const mockUseStreamMetrics = vi.fn()
vi.mock('@/api/stream', () => ({ useStreamMetrics: () => mockUseStreamMetrics() }))

function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
  )
}

const sampleResponse: MetricsResponse = {
  generated_at: '2026-06-02T12:00:00Z',
  models: [
    {
      model_name: 'distilbert-zero-shot',
      status: 'active',
      total_processed: 50,
      correct: 40,
      accuracy: 0.8,
      p50_latency_ms: 55.0,
      p95_latency_ms: 95.5,
      throughput_cps: 0.83,
    },
  ],
}

describe('StreamDashboard', () => {
  beforeEach(() => vi.clearAllMocks())

  it('always renders the page header', () => {
    mockUseStreamMetrics.mockReturnValue({ isLoading: true, error: null, data: undefined })
    render(<StreamDashboard />, { wrapper })
    expect(screen.getByText('Model Comparison')).toBeInTheDocument()
  })

  it('shows skeleton cards while loading, not model cards', () => {
    mockUseStreamMetrics.mockReturnValue({ isLoading: true, error: null, data: undefined })
    render(<StreamDashboard />, { wrapper })
    expect(screen.queryByText('distilbert-zero-shot')).not.toBeInTheDocument()
  })

  it('renders a card for each model when data is present', () => {
    mockUseStreamMetrics.mockReturnValue({ isLoading: false, error: null, data: sampleResponse })
    render(<StreamDashboard />, { wrapper })
    expect(screen.getByText('distilbert-zero-shot')).toBeInTheDocument()
    expect(screen.getByText('80.0%')).toBeInTheDocument()
  })

  it('shows error message when API fails and no data is cached', () => {
    mockUseStreamMetrics.mockReturnValue({
      isLoading: false,
      error: new Error('Network error'),
      data: undefined,
    })
    render(<StreamDashboard />, { wrapper })
    expect(screen.getByText('Could not connect to stream metrics API')).toBeInTheDocument()
  })
})
