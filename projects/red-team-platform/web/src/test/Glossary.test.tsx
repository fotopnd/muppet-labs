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
    expect(screen.getByText('Metrics')).toBeTruthy()
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

  it('renders all 13 wave strategy keys', () => {
    render(<Glossary />, { wrapper })
    const strategies = [
      'AIM', 'evil_confidant', 'few_shot_json', 'refusal_suppression', 'combination_1',
      'dev_mode_v2', 'prefix_injection', 'distractors', 'evil_system_prompt', 'multi_shot_25',
      'gcg', 'base64', 'rot13',
    ]
    for (const s of strategies) {
      expect(screen.getByText(s)).toBeTruthy()
    }
  })

  it('renders sample harm category labels', () => {
    render(<Glossary />, { wrapper })
    expect(screen.getByText('Cyberattack')).toBeTruthy()
    expect(screen.getByText('Violence / Physical Harm')).toBeTruthy()
    expect(screen.getByText('Toxic Language / Hate Speech')).toBeTruthy()
  })
})
