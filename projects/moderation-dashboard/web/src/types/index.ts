export type ModelStatus = 'active' | 'pending_weights'

export type ModelMetrics = {
  model_name: string
  display_name: string
  status: ModelStatus
  event_count: number
  f1: number | null
  precision: number | null
  recall: number | null
  latency_p50: number | null
  latency_p95: number | null
  throughput_per_sec: number | null
}

export type SingleModelVerdict = {
  model_name: string
  predicted_label: number
  confidence: number
  latency_ms: number
  correct: boolean
}

export type EventComparison = {
  event_id: string
  content: string
  category: string
  ground_truth: number
  classifications: SingleModelVerdict[]
}

export type AnomalyFlag = {
  id: string
  window_start: string
  window_end: string
  signal_name: string
  z_score: number
  value: number
  baseline_mean: number
  baseline_std: number
  created_at: string
}

export type StreamMetrics = {
  event_rate_per_sec: number
  category_counts: Record<string, number>
  total_events: number
}

export type CategoryTrend = {
  hour: string
  category: string
  event_count: number
}

export type ModelAccuracyPoint = {
  hour: string
  group: string
  model_name: string
  f1: number
  n: number
}

export type EscalationRatePoint = {
  window_start: string
  escalation_count: number
  total_events: number
  escalation_rate: number
}

export type AnalyticsResponse = {
  category_trends: CategoryTrend[]
  model_accuracy: ModelAccuracyPoint[]
  escalation_rates: EscalationRatePoint[]
}

// From case-queue API
export type CaseListItem = {
  id: string
  content: string
  category: string
  severity: string
  status: string
  source: string
  created_at: string
}

export type CasePage = {
  items: CaseListItem[]
  total: number
  page: number
  page_size: number
}
