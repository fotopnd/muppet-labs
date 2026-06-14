import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Glossary } from '@/pages/Glossary'

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('Glossary', () => {
  it('renders two section headings (Metrics and Harm Categories)', () => {
    render(<Glossary />, { wrapper })
    expect(screen.getByText('Metrics')).toBeTruthy()
    expect(screen.getByText('Harm Categories')).toBeTruthy()
    // Attack Strategies section moved to StrategyExplorer tab
    expect(screen.queryByText('Attack Strategies')).toBeNull()
  })

  it('renders key metric terms', () => {
    render(<Glossary />, { wrapper })
    expect(screen.getByText('ASR')).toBeTruthy()
    expect(screen.getByText('Classifier Score')).toBeTruthy()
    expect(screen.getByText('Jailbreak Success')).toBeTruthy()
    expect(screen.getByText('Latency')).toBeTruthy()
  })

  it('renders sample harm category labels', () => {
    render(<Glossary />, { wrapper })
    expect(screen.getByText('Cyberattack')).toBeTruthy()
    expect(screen.getByText('Violence / Physical Harm')).toBeTruthy()
    expect(screen.getByText('Toxic Language / Hate Speech')).toBeTruthy()
  })
})
