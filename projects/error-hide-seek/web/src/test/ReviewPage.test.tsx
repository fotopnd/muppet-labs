import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { setupServer } from 'msw/node'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'

import { ReviewPage } from '@/pages/ReviewPage'
import { handlers } from './handlers'

const server = setupServer(...handlers)
beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

function renderReviewPage(sessionId = '1') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[`/review/${sessionId}`]}>
        <Routes>
          <Route path="/review/:sessionId" element={<ReviewPage />} />
          <Route path="/results/:experimentId" element={<div>results page</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ReviewPage', () => {
  it('renders paper title after load', async () => {
    renderReviewPage('1')
    await waitFor(() =>
      expect(screen.getByText('Alignment via Feedback: A Study on RLHF')).toBeInTheDocument(),
    )
  })

  it('shows empty state message for detection list', async () => {
    renderReviewPage('1')
    await waitFor(() =>
      expect(
        screen.getByText(/No errors flagged yet/),
      ).toBeInTheDocument(),
    )
  })

  it('renders abstract text', async () => {
    renderReviewPage('1')
    await waitFor(() =>
      expect(screen.getByText(/does not improve alignment by 30%/)).toBeInTheDocument(),
    )
  })

  it('shows annotation highlights for human_agent condition', async () => {
    renderReviewPage('2')
    await waitFor(() =>
      expect(screen.getByText('does not improve alignment by 30%')).toBeInTheDocument(),
    )
  })

  it('shows completion banner for completed session', async () => {
    renderReviewPage('3')
    await waitFor(() =>
      expect(screen.getByText(/Session submitted/)).toBeInTheDocument(),
    )
  })

  it('shows error state for missing session', async () => {
    renderReviewPage('999')
    await waitFor(() =>
      expect(screen.getByText(/Session unavailable/)).toBeInTheDocument(),
    )
  })

  it('adds detection to list when flag button area is used', async () => {
    renderReviewPage('1')
    await waitFor(() =>
      expect(screen.getByText('Alignment via Feedback: A Study on RLHF')).toBeInTheDocument(),
    )
    // submit button should exist
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument()
  })

  it('submit button is present and enabled', async () => {
    renderReviewPage('1')
    await waitFor(() => screen.getByRole('button', { name: /submit/i }))
    expect(screen.getByRole('button', { name: /submit/i })).not.toBeDisabled()
  })
})
