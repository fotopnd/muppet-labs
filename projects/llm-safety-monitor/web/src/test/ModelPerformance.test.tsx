import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi } from 'vitest'
import { ModelPerformance } from '@/pages/ModelPerformance'
import type { MetricsResponse } from '@/types'

const MOCK_DATA: MetricsResponse = {
  models: [
    { model_name: 'pair_classifier', f1: 0.87, precision: 0.85, recall: 0.89, sample_count: 1000 },
    { model_name: 'prompt_detector', f1: 0.91, precision: 0.90, recall: 0.92, sample_count: 800 },
  ],
}

vi.mock('@/api/metrics', () => ({
  useModelMetrics: () => ({ data: MOCK_DATA, isLoading: false, isError: false }),
  useCalibration: () => ({ data: { models: [] }, isLoading: false, isError: false }),
  useDisagreements: () => ({ data: { total: 0, samples: [] }, isLoading: false, isError: false }),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
}

test('renders model names', () => {
  render(<ModelPerformance />, { wrapper })
  expect(screen.getByText('pair_classifier')).toBeInTheDocument()
  expect(screen.getByText('prompt_detector')).toBeInTheDocument()
})

test('renders F1 values formatted as percentages', () => {
  render(<ModelPerformance />, { wrapper })
  expect(screen.getByText('87.0%')).toBeInTheDocument()
  expect(screen.getByText('91.0%')).toBeInTheDocument()
})

test('renders sample counts', () => {
  render(<ModelPerformance />, { wrapper })
  expect(screen.getByText('1,000')).toBeInTheDocument()
})
