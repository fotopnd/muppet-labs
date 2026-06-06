import { render, screen } from '@testing-library/react'
import { CalibrationChart } from '@/components/CalibrationChart'
import type { ModelCalibration } from '@/types'

const DATA: ModelCalibration = {
  model_name: 'pair_classifier',
  bins: [
    { bin_lower: 0.0, bin_upper: 0.1, count: 10, actual_positive_rate: 0.05 },
    { bin_lower: 0.5, bin_upper: 0.6, count: 20, actual_positive_rate: 0.55 },
    { bin_lower: 0.9, bin_upper: 1.0, count: 15, actual_positive_rate: 0.92 },
  ],
}

test('renders model name', () => {
  render(<CalibrationChart data={DATA} />)
  expect(screen.getByText('pair_classifier')).toBeInTheDocument()
})

test('renders without crashing with empty bins', () => {
  render(<CalibrationChart data={{ model_name: 'prompt_detector', bins: [] }} />)
  expect(screen.getByText('prompt_detector')).toBeInTheDocument()
})
