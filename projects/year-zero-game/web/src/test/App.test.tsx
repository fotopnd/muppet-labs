import { describe, test, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from '../App'

function renderApp(route = '/') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[route]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('App routing', () => {
  test('game route renders without crash', () => {
    renderApp('/')
    // StartScreen or Game content visible
    expect(document.body).toBeTruthy()
  })

  test('analytics route renders analytics heading', async () => {
    renderApp('/analytics')
    const heading = await screen.findByText(/year zero/i)
    expect(heading).toBeInTheDocument()
  })
})
