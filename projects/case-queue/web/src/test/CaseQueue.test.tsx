import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { CaseQueue } from '@/pages/CaseQueue'

const mockUseCases = vi.fn()
vi.mock('@/api/cases', () => ({ useCases: (...args: unknown[]) => mockUseCases(...args) }))

function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('CaseQueue', () => {
  beforeEach(() => vi.clearAllMocks())

  it('shows loading state', () => {
    mockUseCases.mockReturnValue({ isLoading: true, isError: false, data: undefined })
    render(<CaseQueue />, { wrapper })
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('shows error message on failure', () => {
    mockUseCases.mockReturnValue({
      isLoading: false,
      isError: true,
      error: new Error('Network error'),
      data: undefined,
    })
    render(<CaseQueue />, { wrapper })
    expect(screen.getByText(/network error/i)).toBeInTheDocument()
  })

  it('shows empty state when no cases', () => {
    mockUseCases.mockReturnValue({
      isLoading: false,
      isError: false,
      data: { items: [], total: 0, page: 1, page_size: 50 },
    })
    render(<CaseQueue />, { wrapper })
    expect(screen.getByText(/no cases/i)).toBeInTheDocument()
  })

  it('renders case rows', () => {
    mockUseCases.mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        items: [
          {
            id: 'abc12345-0000-0000-0000-000000000000',
            category: 'toxic',
            severity: 'high',
            status: 'pending',
            created_at: '2026-01-01T00:00:00Z',
          },
        ],
        total: 1,
        page: 1,
        page_size: 50,
      },
    })
    render(<CaseQueue />, { wrapper })
    expect(screen.getByText('abc12345')).toBeInTheDocument()
    expect(screen.getByText('high')).toBeInTheDocument()
    expect(screen.getByText('pending')).toBeInTheDocument()
  })
})
