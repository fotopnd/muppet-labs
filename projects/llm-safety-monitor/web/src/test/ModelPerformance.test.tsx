import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi } from 'vitest'
import { ModelPerformance } from '@/pages/ModelPerformance'
import type { MetricsResponse, TimeseriesResponse } from '@/types'

const MOCK_METRICS: MetricsResponse = {
  models: [
    { model_name: 'pair_classifier', f1: 0.87, precision: 0.85, recall: 0.89, sample_count: 1000 },
    { model_name: 'prompt_detector', f1: 0.91, precision: 0.90, recall: 0.92, sample_count: 800 },
    { model_name: 'taxonomy_classifier', f1: 0.76, precision: 0.74, recall: 0.78, sample_count: 900 },
  ],
}

const MOCK_TIMESERIES: TimeseriesResponse = {
  bucket_minutes: 5,
  models: [
    {
      model_name: 'pair_classifier',
      points: [
        { bucket: '2026-06-06T12:00:00Z', f1: 0.85, precision: 0.84, recall: 0.86, sample_count: 50 },
        { bucket: '2026-06-06T12:05:00Z', f1: 0.87, precision: 0.85, recall: 0.89, sample_count: 100 },
      ],
    },
    { model_name: 'prompt_detector', points: [] },
    { model_name: 'taxonomy_classifier', points: [] },
  ],
}

vi.mock('@/api/metrics', () => ({
  useModelMetrics: () => ({ data: MOCK_METRICS, isLoading: false, isError: false }),
  useMetricsTimeseries: () => ({ data: MOCK_TIMESERIES, isLoading: false, isError: false }),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
}

test('renders model names in summary table', () => {
  render(<ModelPerformance />, { wrapper })
  expect(screen.getByText('pair_classifier')).toBeInTheDocument()
  expect(screen.getByText('prompt_detector')).toBeInTheDocument()
  expect(screen.getByText('taxonomy_classifier')).toBeInTheDocument()
})

test('renders F1 values as percentages', () => {
  render(<ModelPerformance />, { wrapper })
  expect(screen.getByText('87.0%')).toBeInTheDocument()
  expect(screen.getByText('91.0%')).toBeInTheDocument()
  expect(screen.getByText('76.0%')).toBeInTheDocument()
})

test('renders three chart headings', () => {
  render(<ModelPerformance />, { wrapper })
  expect(screen.getByText('F1 by Model')).toBeInTheDocument()
  expect(screen.getByText('Precision by Model')).toBeInTheDocument()
  expect(screen.getByText('Recall by Model')).toBeInTheDocument()
})

test('renders sample count', () => {
  render(<ModelPerformance />, { wrapper })
  expect(screen.getByText('1,000')).toBeInTheDocument()
})
