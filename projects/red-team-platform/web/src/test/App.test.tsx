import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '@/App'

describe('App', () => {
  it('renders all tab buttons', async () => {
    render(<App />)
    const nav = screen.getByRole('navigation')
    expect(nav).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Strategy Explorer' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Analytics' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Failure Clusters' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Bias Heatmap' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Glossary' })).toBeInTheDocument()
  })
})
