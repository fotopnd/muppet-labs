import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { HumanReview } from '@/pages/HumanReview'
import type { EscalationCase } from '@/types'

const CASE_DATA: EscalationCase[] = [
  {
    id: 'esc-1',
    event_id: 'evt-1',
    content: 'Offensive content example that is fairly long to test truncation',
    category: 'toxic',
    escalation_reason: 'low_confidence',
    confidence_max: 0.45,
    created_at: '2026-06-03T10:00:00Z',
    action: null,
    notes: null,
  },
]

const server = setupServer(
  http.get('http://localhost:8002/cases', () => HttpResponse.json(CASE_DATA)),
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}

describe('HumanReview', () => {
  it('renders escalation rows with data', async () => {
    renderWithQuery(<HumanReview />)
    const content = await screen.findByText(/Offensive content example/)
    expect(content).toBeInTheDocument()
  })

  it('renders case count with pending indicator', async () => {
    renderWithQuery(<HumanReview />)
    const count = await screen.findByText(/1 case/)
    expect(count).toBeInTheDocument()
  })

  it('shows approve and reject buttons for undecided cases', async () => {
    renderWithQuery(<HumanReview />)
    const approveBtn = await screen.findByText('Approve')
    expect(approveBtn).toBeInTheDocument()
    const rejectBtn = screen.getByText('Reject')
    expect(rejectBtn).toBeInTheDocument()
  })

  it('shows empty state when no escalations', async () => {
    server.use(
      http.get('http://localhost:8002/cases', () => HttpResponse.json([])),
    )
    renderWithQuery(<HumanReview />)
    const empty = await screen.findByText('No escalations yet')
    expect(empty).toBeInTheDocument()
  })

  it('shows error when escalation API is unreachable', async () => {
    server.use(
      http.get('http://localhost:8002/cases', () => HttpResponse.error()),
    )
    renderWithQuery(<HumanReview />)
    const error = await screen.findByText('Failed to load escalations')
    expect(error).toBeInTheDocument()
  })
})
