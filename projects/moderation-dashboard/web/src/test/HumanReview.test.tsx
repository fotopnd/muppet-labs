import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { HumanReview } from '@/pages/HumanReview'
import type { CasePage } from '@/types'

const CASE_DATA: CasePage = {
  items: [
    {
      id: 'case-1',
      content: 'Offensive content example that is fairly long to test truncation',
      category: 'toxic',
      severity: 'medium',
      status: 'pending',
      source: 'moderation-dashboard',
      created_at: '2026-06-03T10:00:00Z',
    },
  ],
  total: 1,
  page: 1,
  page_size: 50,
}

const server = setupServer(
  http.get('http://localhost:8000/cases', () => HttpResponse.json(CASE_DATA)),
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

  it('renders case count', async () => {
    renderWithQuery(<HumanReview />)
    const count = await screen.findByText('1 pending case')
    expect(count).toBeInTheDocument()
  })

  it('shows empty state when no cases', async () => {
    server.use(
      http.get('http://localhost:8000/cases', () =>
        HttpResponse.json({ items: [], total: 0, page: 1, page_size: 50 }),
      ),
    )
    renderWithQuery(<HumanReview />)
    const empty = await screen.findByText('No pending escalations')
    expect(empty).toBeInTheDocument()
  })

  it('shows error when case queue is unreachable', async () => {
    server.use(
      http.get('http://localhost:8000/cases', () => HttpResponse.error()),
    )
    renderWithQuery(<HumanReview />)
    const error = await screen.findByText('Case queue unavailable')
    expect(error).toBeInTheDocument()
  })
})
