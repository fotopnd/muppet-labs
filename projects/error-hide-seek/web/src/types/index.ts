export type Paper = {
  id: number
  arxiv_id: string
  title: string
  abstract: string
  categories: string
  fetched_at: string
}

export type PapersPage = {
  items: Paper[]
  total: number
  offset: number
  limit: number
}

export type ExperimentPaper = {
  paper_id: number
  title: string
  arxiv_id: string
  condition: 'unaided' | 'agent_only' | 'human_agent'
}

export type Experiment = {
  id: number
  name: string
  description: string
  created_at: string
  papers: ExperimentPaper[]
}

export type ExperimentSummary = {
  id: number
  name: string
  description: string
  created_at: string
  paper_count: number
}

export type Annotation = {
  id: number
  text_excerpt: string
  confidence: 'high' | 'medium' | 'low'
  reason: string
}

export type AutoScoredResult = {
  true_positives: number
  false_positives: number
  tpr: number
  fpr: number
}

export type Session = {
  session_id: number
  experiment_id: number
  paper_id: number
  paper_title: string
  condition: 'unaided' | 'agent_only' | 'human_agent'
  status: 'open' | 'completed'
  abstract_text: string
  annotations: Annotation[]
  scored_result: AutoScoredResult | null
}

export type SessionListItem = {
  session_id: number
  condition: 'unaided' | 'agent_only' | 'human_agent'
  status: 'open' | 'completed'
}

export type ReviewConfirmOut = {
  session_id: number
  status: string
}

export type DetectionIn = {
  text_excerpt: string
  note: string | null
}

export type ReviewSubmitBody = {
  session_id: number
  detections: DetectionIn[]
}

export type CategoryResult = {
  category: string
  planted_count: number
  detected_count: number
  tpr: number | null
}

export type ConditionResult = {
  condition: 'unaided' | 'agent_only' | 'human_agent'
  sessions_total: number
  sessions_complete: number
  true_positive_rate: number | null
  false_positive_rate: number | null
  by_category: CategoryResult[]
}

export type ExperimentResults = {
  experiment_id: number
  uplift: number | null
  conditions: ConditionResult[]
}
