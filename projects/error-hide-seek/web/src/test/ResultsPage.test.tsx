import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { setupServer } from 'msw/node'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'

import { ResultsPage } from '@/pages/ResultsPage'
import { handlers } from './handlers'

const server = setupServer(...handlers)
beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

function renderResultsPage(experimentId = '1') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[`/results/${experimentId}`]}>
        <Routes>
          <Route path="/results/:experimentId" element={<ResultsPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ResultsPage', () => {
  it('shows positive uplift in emerald when uplift > 0', async () => {
    renderResultsPage('1')
    await waitFor(() => expect(screen.getByText('+15.0%')).toBeInTheDocument())
    expect(screen.getByText('+15.0%')).toHaveClass('text-success')
  })

  it('shows Human Uplift label', async () => {
    renderResultsPage('1')
    await waitFor(() => expect(screen.getByText('Human Uplift')).toBeInTheDocument())
  })

  it('shows "Results incomplete" when uplift is null', async () => {
    renderResultsPage('2')
    await waitFor(() => expect(screen.getByText('Results incomplete')).toBeInTheDocument())
  })

  it('renders condition table headers', async () => {
    renderResultsPage('1')
    await waitFor(() =>
      expect(screen.getByText('Detection Rates by Condition')).toBeInTheDocument(),
    )
    expect(screen.getAllByText('Unaided').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Agent Only').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Human + Agent').length).toBeGreaterThan(0)
  })

  it('renders TPR values in the table', async () => {
    renderResultsPage('1')
    await waitFor(() => expect(screen.getAllByText('33.0%').length).toBeGreaterThan(0))
    expect(screen.getAllByText('67.0%').length).toBeGreaterThan(0)
    expect(screen.getByText('48.0%')).toBeInTheDocument()
  })

  it('renders category breakdown', async () => {
    renderResultsPage('1')
    await waitFor(() => expect(screen.getByText('By Error Category')).toBeInTheDocument())
    expect(screen.getByText('Inverted Conclusion')).toBeInTheDocument()
  })

  it('shows — for incomplete conditions', async () => {
    renderResultsPage('2')
    await waitFor(() => expect(screen.getByText('Results incomplete')).toBeInTheDocument())
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })
})
