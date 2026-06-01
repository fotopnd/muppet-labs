import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { CaseDetail } from '@/pages/CaseDetail'

const mockUseCase = vi.fn()
const mockUseCreateDecision = vi.fn()
vi.mock('@/api/cases', () => ({
  useCase: (...args: unknown[]) => mockUseCase(...args),
  useCreateDecision: (...args: unknown[]) => mockUseCreateDecision(...args),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={['/cases/test-id']}>
        <Routes>
          <Route path="/cases/:id" element={children} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

const sampleCase = {
  id: 'test-id',
  content: 'You are absolutely worthless.',
  category: 'toxic' as const,
  severity: 'high' as const,
  status: 'pending' as const,
  source: 'test',
  meta: {},
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  decisions: [],
}

describe('CaseDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseCreateDecision.mockReturnValue({ mutateAsync: vi.fn(), isPending: false, isError: false })
  })

  it('shows loading state', () => {
    mockUseCase.mockReturnValue({ isLoading: true, isError: false, data: undefined })
    render(<CaseDetail />, { wrapper })
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('renders case content', () => {
    mockUseCase.mockReturnValue({ isLoading: false, isError: false, data: sampleCase })
    render(<CaseDetail />, { wrapper })
    expect(screen.getByText('You are absolutely worthless.')).toBeInTheDocument()
    expect(screen.getByText('pending')).toBeInTheDocument()
  })

  it('shows decision form', () => {
    mockUseCase.mockReturnValue({ isLoading: false, isError: false, data: sampleCase })
    render(<CaseDetail />, { wrapper })
    expect(screen.getByRole('button', { name: /submit decision/i })).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/required/i)).toBeInTheDocument()
  })

  it('shows prior decisions', () => {
    const caseWithDecision = {
      ...sampleCase,
      decisions: [
        {
          id: 'dec-1',
          actor_id: 'alice',
          actor_role: 'reviewer' as const,
          action: 'approve' as const,
          notes: 'Looks fine.',
          created_at: '2026-01-02T00:00:00Z',
        },
      ],
    }
    mockUseCase.mockReturnValue({ isLoading: false, isError: false, data: caseWithDecision })
    render(<CaseDetail />, { wrapper })
    expect(screen.getByText('alice')).toBeInTheDocument()
    expect(screen.getByText('Looks fine.')).toBeInTheDocument()
  })
})
