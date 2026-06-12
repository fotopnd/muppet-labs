import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import MetricsTable from '@/components/MetricsTable'

describe('MetricsTable', () => {
  it('renders all label/value pairs', () => {
    const rows = [
      { label: 'F1 Score', value: '0.818' },
      { label: 'Precision', value: '0.792' },
    ]
    render(<MetricsTable rows={rows} />)
    expect(screen.getByText('F1 Score')).toBeInTheDocument()
    expect(screen.getByText('0.818')).toBeInTheDocument()
    expect(screen.getByText('Precision')).toBeInTheDocument()
    expect(screen.getByText('0.792')).toBeInTheDocument()
  })

  it('renders nothing when rows is empty', () => {
    const { container } = render(<MetricsTable rows={[]} />)
    expect(container.firstChild).toBeNull()
  })
})
