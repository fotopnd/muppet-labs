import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi } from 'vitest'
import { TaxonomyTrends } from '@/pages/TaxonomyTrends'
import type { TaxonomyTimeseriesResponse } from '@/types'

const MOCK_DATA: TaxonomyTimeseriesResponse = {
  bucket_minutes: 5,
  categories: ['violence_and_physical_harm', 'toxic_language_hate_speech', 'fraud_assisting_illegal_activities'],
  buckets: [
    {
      bucket: '2026-06-06T12:00:00Z',
      counts: { violence_and_physical_harm: 12, toxic_language_hate_speech: 8, fraud_assisting_illegal_activities: 5 },
    },
    {
      bucket: '2026-06-06T12:05:00Z',
      counts: { violence_and_physical_harm: 15, toxic_language_hate_speech: 10, fraud_assisting_illegal_activities: 7 },
    },
  ],
}

vi.mock('@/api/metrics', () => ({
  useTaxonomyTimeseries: () => ({ data: MOCK_DATA, isLoading: false, isError: false }),
  useModelMetrics: () => ({ data: { models: [] }, isLoading: false, isError: false }),
  useMetricsTimeseries: () => ({ data: { models: [], bucket_minutes: 5 }, isLoading: false, isError: false }),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
}

test('renders main heading', () => {
  render(<TaxonomyTrends />, { wrapper })
  expect(screen.getByText('Harm Category Trends')).toBeInTheDocument()
})

test('renders bucket size label', () => {
  render(<TaxonomyTrends />, { wrapper })
  expect(screen.getByText('5-min buckets')).toBeInTheDocument()
})

test('renders all four group sub-chart headings', () => {
  render(<TaxonomyTrends />, { wrapper })
  expect(screen.getByText('Hate & Violence')).toBeInTheDocument()
  expect(screen.getByText('Privacy & IP')).toBeInTheDocument()
  expect(screen.getByText('Cybercrime')).toBeInTheDocument()
  expect(screen.getByText('Misinformation')).toBeInTheDocument()
})

test('renders overview group heading', () => {
  render(<TaxonomyTrends />, { wrapper })
  expect(screen.getByText('All Groups')).toBeInTheDocument()
})
