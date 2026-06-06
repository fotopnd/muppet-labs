import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi } from 'vitest'
import { Calibration } from '@/pages/Calibration'
import type { CalibrationResponse } from '@/types'

const MOCK_DATA: CalibrationResponse = {
  models: [
    {
      model_name: 'pair_classifier',
      bins: [{ bin_lower: 0.0, bin_upper: 0.1, count: 10, actual_positive_rate: 0.05 }],
    },
  ],
}

vi.mock('@/api/metrics', () => ({
  useModelMetrics: () => ({ data: { models: [] }, isLoading: false, isError: false }),
  useCalibration: () => ({ data: MOCK_DATA, isLoading: false, isError: false }),
  useDisagreements: () => ({ data: { total: 0, samples: [] }, isLoading: false, isError: false }),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
}

test('renders calibration chart for each model', () => {
  render(<Calibration />, { wrapper })
  expect(screen.getByText('pair_classifier')).toBeInTheDocument()
})

test('shows explanatory text', () => {
  render(<Calibration />, { wrapper })
  expect(screen.getByText(/reliability diagrams/i)).toBeInTheDocument()
})
