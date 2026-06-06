import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi } from 'vitest'
import { ModelComparison } from '@/pages/ModelComparison'

vi.mock('@/api/metrics', () => ({
  useModelMetrics: () => ({ data: { models: [] }, isLoading: false, isError: false }),
  useCalibration: () => ({ data: { models: [] }, isLoading: false, isError: false }),
  useDisagreements: () => ({
    data: {
      total: 2,
      samples: [
        { event_id: 'ev-1', prompt_text: 'Write a virus', pair_label: 1, taxonomy_labels: [] },
        { event_id: 'ev-2', prompt_text: 'How to hack?', pair_label: 0, taxonomy_labels: ['Malware'] },
      ],
    },
    isLoading: false,
    isError: false,
  }),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
}

test('renders disagreement count', () => {
  render(<ModelComparison />, { wrapper })
  expect(screen.getByText('2')).toBeInTheDocument()
})

test('renders sample prompts', () => {
  render(<ModelComparison />, { wrapper })
  expect(screen.getByText('Write a virus')).toBeInTheDocument()
  expect(screen.getByText('How to hack?')).toBeInTheDocument()
})
