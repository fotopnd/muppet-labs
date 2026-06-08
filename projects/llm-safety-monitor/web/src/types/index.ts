export type SourceDataset = 'hh-rlhf' | 'wildguard' | 'advbench' | 'jailbreakbench' | 'live' | 'red_team'
export type SourceDatasetFilter = SourceDataset | 'all'

export type EscalationReason =
  | 'JAILBREAK'
  | 'BENIGN_HARMFUL'
  | 'LOG_ONLY'
  | 'MODEL_DISAGREEMENT'
  | 'ADVERSARIAL_PROMPT_FLAGGED'

export type VerdictEntry = {
  model_name: string
  predicted_label: number
  confidence: number
  taxonomy_labels: string[] | null
}

export type RecentEvent = {
  event_id: string
  prompt_text: string
  response_text: string | null
  source_dataset: SourceDataset
  verdicts: VerdictEntry[]
  escalation_reason: EscalationReason | null
}

export type StreamResponse = { events: RecentEvent[] }

export type ModelMetrics = {
  model_name: string
  f1: number
  precision: number
  recall: number
  sample_count: number
}

export type MetricsResponse = { models: ModelMetrics[] }

// Performance timeseries — matches GET /metrics/timeseries?bucket_minutes=60
export type MetricPoint = {
  bucket: string      // ISO 8601 datetime
  f1: number
  precision: number
  recall: number
  sample_count: number
}

export type ModelTimeseries = {
  model_name: string
  points: MetricPoint[]
}

export type TimeseriesResponse = {
  models: ModelTimeseries[]
  bucket_minutes: number
}

// Taxonomy timeseries — matches GET /metrics/taxonomy/timeseries?bucket_minutes=60
export type TaxonomyBucket = {
  bucket: string      // ISO 8601 datetime
  counts: Record<string, number>
}

export type TaxonomyTimeseriesResponse = {
  buckets: TaxonomyBucket[]
  categories: string[]
  bucket_minutes: number
}

// Escalation queue — matches GET /cases (DisagreementsResponse shape on backend)
export type EscalationQueueItem = {
  event_id: string
  prompt_text: string
  pair_label: number | null
  taxonomy_labels: string[] | null
  escalation_reason: EscalationReason | null
}

export type EscalationQueueResponse = {
  total: number
  samples: EscalationQueueItem[]
}

// Calibration — matches GET /metrics/calibration
export type CalibrationBin = {
  bin_lower: number
  bin_upper: number
  count: number
  actual_positive_rate: number
}

export type ModelCalibration = {
  model_name: string
  bins: CalibrationBin[]
}

export type CalibrationResponse = {
  models: ModelCalibration[]
}

// Human review decision — matches POST /cases/{id}/decide
export type ReviewDecisionResponse = {
  case_id: string
  decision: string
  acknowledged: boolean
}
