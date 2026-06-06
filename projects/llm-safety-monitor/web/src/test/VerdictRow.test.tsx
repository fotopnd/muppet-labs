import { render, screen } from '@testing-library/react'
import { VerdictRow } from '@/components/VerdictRow'
import type { VerdictEntry } from '@/types'

const VERDICTS: VerdictEntry[] = [
  { model_name: 'pair_classifier', predicted_label: 1, confidence: 0.9, taxonomy_labels: null },
  { model_name: 'prompt_detector', predicted_label: 1, confidence: 0.85, taxonomy_labels: null },
  { model_name: 'taxonomy_classifier', predicted_label: 1, confidence: 0.7, taxonomy_labels: ['Hate', 'Violence'] },
]

test('renders pair verdict', () => {
  render(<VerdictRow verdicts={VERDICTS} />)
  expect(screen.getByText('Unsafe')).toBeInTheDocument()
})

test('renders prompt verdict', () => {
  render(<VerdictRow verdicts={VERDICTS} />)
  expect(screen.getByText('Adversarial')).toBeInTheDocument()
})

test('renders taxonomy labels', () => {
  render(<VerdictRow verdicts={VERDICTS} />)
  expect(screen.getByText('Hate')).toBeInTheDocument()
  expect(screen.getByText('Violence')).toBeInTheDocument()
})

test('shows safe and benign when labels are 0', () => {
  const safe: VerdictEntry[] = [
    { model_name: 'pair_classifier', predicted_label: 0, confidence: 0.1, taxonomy_labels: null },
    { model_name: 'prompt_detector', predicted_label: 0, confidence: 0.1, taxonomy_labels: null },
    { model_name: 'taxonomy_classifier', predicted_label: 0, confidence: 0.1, taxonomy_labels: [] },
  ]
  render(<VerdictRow verdicts={safe} />)
  expect(screen.getByText('Safe')).toBeInTheDocument()
  expect(screen.getByText('Benign')).toBeInTheDocument()
  expect(screen.getByText('none')).toBeInTheDocument()
})

test('handles missing models with dash', () => {
  render(<VerdictRow verdicts={[]} />)
  const dashes = screen.getAllByText('—')
  expect(dashes.length).toBe(3)
})
