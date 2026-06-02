import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ModelMetricsCard } from '@/components/ModelMetricsCard'
import type { ModelMetrics } from '@/types/stream'

const activeMetrics: ModelMetrics = {
  model_name: 'distilbert-zero-shot',
  status: 'active',
  total_processed: 100,
  correct: 80,
  accuracy: 0.8,
  p50_latency_ms: 55.0,
  p95_latency_ms: 95.5,
  throughput_cps: 1.67,
}

const pendingMetrics: ModelMetrics = {
  model_name: 'distilbert-finetuned',
  status: 'pending_weights',
  total_processed: 0,
  correct: null,
  accuracy: null,
  p50_latency_ms: 0,
  p95_latency_ms: 0,
  throughput_cps: 0,
}

describe('ModelMetricsCard — active state', () => {
  it('renders model name and Active badge', () => {
    render(<ModelMetricsCard metrics={activeMetrics} />)
    expect(screen.getByText('distilbert-zero-shot')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('renders formatted accuracy', () => {
    render(<ModelMetricsCard metrics={activeMetrics} />)
    expect(screen.getByText('80.0%')).toBeInTheDocument()
  })

  it('renders N/A when accuracy is null', () => {
    render(<ModelMetricsCard metrics={{ ...activeMetrics, accuracy: null, correct: null }} />)
    expect(screen.getByText('N/A')).toBeInTheDocument()
  })

  it('renders p50 latency and processed count', () => {
    render(<ModelMetricsCard metrics={activeMetrics} />)
    expect(screen.getByText('55.0ms')).toBeInTheDocument()
    expect(screen.getByText(/100.*processed/)).toBeInTheDocument()
  })
})

describe('ModelMetricsCard — pending_weights state', () => {
  it('renders model name and Pending Weights badge', () => {
    render(<ModelMetricsCard metrics={pendingMetrics} />)
    expect(screen.getByText('distilbert-finetuned')).toBeInTheDocument()
    expect(screen.getByText('Pending Weights')).toBeInTheDocument()
  })

  it('shows awaiting message and hides metric rows', () => {
    render(<ModelMetricsCard metrics={pendingMetrics} />)
    expect(screen.getByText(/awaiting fine-tuned weights/i)).toBeInTheDocument()
    expect(screen.queryByText('Accuracy')).not.toBeInTheDocument()
  })
})
