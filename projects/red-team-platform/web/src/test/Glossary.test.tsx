import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Glossary } from '@/pages/Glossary'

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('Glossary', () => {
  it('renders three section headings', () => {
    render(<Glossary />, { wrapper })
    expect(screen.getByText('Metrics & Scoring')).toBeTruthy()
    expect(screen.getByText('Attack Strategies')).toBeTruthy()
    expect(screen.getByText('Harm Categories')).toBeTruthy()
  })

  it('renders key metric terms', () => {
    render(<Glossary />, { wrapper })
    expect(screen.getByText('ASR')).toBeTruthy()
    expect(screen.getByText('Classifier Score')).toBeTruthy()
    expect(screen.getByText('Jailbreak Success')).toBeTruthy()
    expect(screen.getByText('Latency')).toBeTruthy()
  })

  it('renders sample harm category labels from new taxonomy', () => {
    render(<Glossary />, { wrapper })
    expect(screen.getByText('Cybercrime & Intrusion')).toBeTruthy()
    expect(screen.getByText('Violence')).toBeTruthy()
    expect(screen.getByText('Hate & Discrimination')).toBeTruthy()
  })

  it('renders strategy keys in the attack strategies table', () => {
    render(<Glossary />, { wrapper })
    // AIM appears as both key and name — use getAllByText
    expect(screen.getAllByText('AIM').length).toBeGreaterThan(0)
    expect(screen.getByText('evil_confidant')).toBeTruthy()
    expect(screen.getByText('base64')).toBeTruthy()
  })
})
