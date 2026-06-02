import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuditLog } from '@/pages/AuditLog'

const mockUseAuditLog = vi.fn()
const mockUseAuditActors = vi.fn()
vi.mock('@/api/audit', () => ({
  useAuditLog: (...args: unknown[]) => mockUseAuditLog(...args),
  useAuditActors: (...args: unknown[]) => mockUseAuditActors(...args),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('AuditLog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseAuditActors.mockReturnValue({ data: undefined })
  })

  it('shows loading state', () => {
    mockUseAuditLog.mockReturnValue({ isLoading: true, isError: false, data: undefined })
    render(<AuditLog />, { wrapper })
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('shows empty state', () => {
    mockUseAuditLog.mockReturnValue({
      isLoading: false,
      isError: false,
      data: { items: [], total: 0, page: 1, page_size: 50 },
    })
    render(<AuditLog />, { wrapper })
    expect(screen.getByText(/no decisions/i)).toBeInTheDocument()
  })

  it('renders audit entries', () => {
    mockUseAuditLog.mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        items: [
          {
            id: 'entry-1',
            case_id: 'case-abcd1234-0000-0000-0000-000000000000',
            actor_id: 'alice',
            actor_role: 'reviewer',
            action: 'approve',
            notes: 'Approved this one.',
            created_at: '2026-01-01T12:00:00Z',
          },
        ],
        total: 1,
        page: 1,
        page_size: 50,
      },
    })
    render(<AuditLog />, { wrapper })
    expect(screen.getByText('alice')).toBeInTheDocument()
    expect(screen.getByText('approve')).toBeInTheDocument()
    expect(screen.getByText('Approved this one.')).toBeInTheDocument()
  })
})
