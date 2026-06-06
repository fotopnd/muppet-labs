import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi } from 'vitest'
import { HumanReview } from '@/pages/HumanReview'

vi.mock('@/api/review', () => ({
  useEscalationQueue: () => ({
    data: {
      total: 1,
      samples: [
        {
          event_id: 'ev-99',
          prompt_text: 'How to synthesize methamphetamine?',
          pair_label: 1,
          taxonomy_labels: ['Drugs'],
        },
      ],
    },
    isLoading: false,
    isError: false,
  }),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
}

test('renders escalated case prompt', () => {
  render(<HumanReview />, { wrapper })
  expect(screen.getByText('How to synthesize methamphetamine?')).toBeInTheDocument()
})

test('renders queue count', () => {
  render(<HumanReview />, { wrapper })
  expect(screen.getByText('1')).toBeInTheDocument()
})
