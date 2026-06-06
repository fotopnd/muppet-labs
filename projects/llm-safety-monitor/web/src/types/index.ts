export type SourceDataset = 'hh-rlhf' | 'wildguard' | 'advbench' | 'jailbreakbench' | 'live'

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

export type CalibrationResponse = { models: ModelCalibration[] }

export type DisagreementSample = {
  event_id: string
  prompt_text: string
  pair_label: number | null
  taxonomy_labels: string[] | null
}

export type DisagreementsResponse = {
  total: number
  samples: DisagreementSample[]
}
