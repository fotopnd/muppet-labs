import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '@/App'

describe('App', () => {
  it('renders all tab buttons', async () => {
    render(<App />)
    const nav = screen.getByRole('navigation')
    expect(nav).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Attack Browser' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Coverage Heatmap' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Strategy Comparison' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Regression Tracker' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sample Review' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Failure Clusters' })).toBeInTheDocument()
  })
})
