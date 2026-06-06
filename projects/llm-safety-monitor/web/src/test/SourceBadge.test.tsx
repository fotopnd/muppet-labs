import { render, screen } from '@testing-library/react'
import { SourceBadge } from '@/components/SourceBadge'

test('renders hh-rlhf label', () => {
  render(<SourceBadge source="hh-rlhf" />)
  expect(screen.getByText('HH-RLHF')).toBeInTheDocument()
})

test('renders advbench label', () => {
  render(<SourceBadge source="advbench" />)
  expect(screen.getByText('AdvBench')).toBeInTheDocument()
})

test('renders live label', () => {
  render(<SourceBadge source="live" />)
  expect(screen.getByText('Live')).toBeInTheDocument()
})

test('has data-testid', () => {
  render(<SourceBadge source="wildguard" />)
  expect(screen.getByTestId('source-badge')).toBeInTheDocument()
})
