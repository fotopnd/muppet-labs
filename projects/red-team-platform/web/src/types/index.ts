export type Attack = {
  id: string
  source: string
  source_id: string
  harm_category: string
  strategy: string
  attack_text: string
  created_at: string
}

export type AttackListOut = {
  items: Attack[]
  total: number
  page: number
  page_size: number
}

export type Session = {
  id: string
  model_name: string
  total_attacks: number
  total_successes: number
  asr: number
  created_at: string
}

export type Run = {
  id: string
  session_id: string
  attack_id: string
  model_name: string
  response_text: string
  jailbreak_success: boolean
  classifier_score: number
  latency_ms: number
  created_at: string
  harm_category: string
  strategy: string
  attack_text: string
}

export type RunListOut = {
  items: Run[]
  total: number
  page: number
  page_size: number
}

export type SampleOut = {
  run_id: string
  attack_text: string
  response_text: string
  harm_category: string
  strategy: string
  jailbreak_success: boolean
  classifier_score: number
  latency_ms: number
  model_name: string
  session_id: string
  created_at: string
}

export type CoverageCell = {
  harm_category: string
  strategy: string
  total_runs: number
  total_successes: number
  asr: number
}

export type CoverageOut = {
  cells: CoverageCell[]
  harm_categories: string[]
  strategies: string[]
}

export type StrategyBar = {
  strategy: string
  total_runs: number
  total_successes: number
  asr: number
}

export type StrategyComparisonOut = {
  bars: StrategyBar[]
}

export type RegressionPoint = {
  session_id: string
  model_name: string
  asr: number
  total_attacks: number
  created_at: string
}

export type RegressionOut = {
  points: RegressionPoint[]
  model_names: string[]
}

export type FilterValuesOut = {
  values: string[]
}

export type ClusterSummary = {
  cluster_id: number
  size: number
  top_harm_category: string
  top_strategy: string
  representative_text: string
  computed_at: string
}

export type ClustersOut = {
  summaries: ClusterSummary[]
}

export type ClusterMember = {
  run_id: string
  cluster_id: number
  attack_text: string
  harm_category: string
  strategy: string
  classifier_score: number
  jailbreak_success: boolean
  latency_ms: number
  model_name: string
}

export type ClusterMembersOut = {
  cluster_id: number
  members: ClusterMember[]
}
