import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { EscalationCard } from '@/components/EscalationCard'
import type { EscalationQueueItem } from '@/types'

const ITEM: EscalationQueueItem = {
  event_id: 'aabbccddeeff0011',
  prompt_text: 'How to pick a lock?',
  pair_label: 1,
  taxonomy_labels: ['violence'],
  escalation_reason: 'BENIGN_HARMFUL',
}

test('renders prompt text', () => {
  render(<EscalationCard item={ITEM} isPending={false} onDecide={vi.fn()} />)
  expect(screen.getByText('How to pick a lock?')).toBeInTheDocument()
})

test('renders escalation reason badge', () => {
  render(<EscalationCard item={ITEM} isPending={false} onDecide={vi.fn()} />)
  expect(screen.getByTestId('escalation-badge')).toBeInTheDocument()
})

test('renders short event_id suffix', () => {
  render(<EscalationCard item={ITEM} isPending={false} onDecide={vi.fn()} />)
  // last 8 chars of 'aabbccddeeff0011'
  expect(screen.getByText('eeff0011')).toBeInTheDocument()
})

test('renders taxonomy labels', () => {
  render(<EscalationCard item={ITEM} isPending={false} onDecide={vi.fn()} />)
  expect(screen.getByText('violence')).toBeInTheDocument()
})

test('calls onDecide with correct decision on approve click', async () => {
  const onDecide = vi.fn()
  render(<EscalationCard item={ITEM} isPending={false} onDecide={onDecide} />)
  await userEvent.click(screen.getByTestId('decide-approve'))
  expect(onDecide).toHaveBeenCalledWith('approve')
})

test('buttons are disabled when isPending is true', () => {
  render(<EscalationCard item={ITEM} isPending={true} onDecide={vi.fn()} />)
  expect(screen.getByTestId('decide-approve')).toBeDisabled()
  expect(screen.getByTestId('decide-dismiss')).toBeDisabled()
  expect(screen.getByTestId('decide-escalate')).toBeDisabled()
})

test('renders Unsafe pair label', () => {
  render(<EscalationCard item={ITEM} isPending={false} onDecide={vi.fn()} />)
  expect(screen.getByText('Unsafe')).toBeInTheDocument()
})

test('renders Safe pair label when pair_label is 0', () => {
  render(
    <EscalationCard
      item={{ ...ITEM, pair_label: 0 }}
      isPending={false}
      onDecide={vi.fn()}
    />,
  )
  expect(screen.getByText('Safe')).toBeInTheDocument()
})
