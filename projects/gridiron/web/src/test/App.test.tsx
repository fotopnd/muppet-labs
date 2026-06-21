import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import StatusBadge from '@/components/StatusBadge'

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

test('StatusBadge renders live state', () => {
  render(<StatusBadge status="live" />, { wrapper })
  expect(screen.getByText('LIVE')).toBeInTheDocument()
})

test('StatusBadge renders complete state', () => {
  render(<StatusBadge status="complete" />, { wrapper })
  expect(screen.getByText('Final')).toBeInTheDocument()
})

test('StatusBadge renders scheduled state', () => {
  render(<StatusBadge status="scheduled" />, { wrapper })
  expect(screen.getByText('Scheduled')).toBeInTheDocument()
})
