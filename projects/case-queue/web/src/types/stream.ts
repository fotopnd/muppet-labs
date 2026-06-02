export type ModelStatus = 'active' | 'pending_weights'

export type ModelMetrics = {
  model_name: string
  status: ModelStatus
  total_processed: number
  correct: number | null
  accuracy: number | null
  p50_latency_ms: number
  p95_latency_ms: number
  throughput_cps: number
}

export type MetricsResponse = {
  models: ModelMetrics[]
  generated_at: string
}
