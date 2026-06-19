export type Verdict = 'ACCEPT' | 'REJECT' | 'ESCALATE'
export type AgentCondition = 'none' | 'tier_1' | 'tier_2' | 'tier_3'
export type GameOverReason = 'SESSION_COMPLETE'

export interface ResourceState {
  escalationsRemaining: number
}

export interface Card {
  id: number
  promptText: string
  responseText: string
  harmCategory: string
  phase: number
  generationTier: number
  isHarmful: boolean
  gorkVerdict: boolean | null
  gorkConfidence: number | null
  gorkReasoning: string | null
  agentCondition: AgentCondition
}

export interface PendingDecision {
  documentId: number
  agentCondition: AgentCondition
  playerVerdict: Verdict
  playerCorrect: boolean
  latencyMs: number
  agreedWithAgent: boolean | null
  resources: ResourceState
  gameDay: number
  phase: number
  categoryTier: number
}

export type GamePhase =
  | 'start'
  | 'lore'
  | 'playing'
  | 'game_over'

export interface GameState {
  phase: GamePhase
  sessionId: number | null
  cardsPlayed: number
  cardStartedAt: number | null
  currentCard: Card | null
  cardPool: Card[]
  pendingDecisions: PendingDecision[]
  resources: ResourceState
  gameOverReason: GameOverReason | null
  totalDecisions: number
  totalCorrect: number
  totalEscalated: number
}

export type GameAction =
  | { type: 'START_SESSION'; sessionId: number; cards: Card[] }
  | { type: 'SWIPE'; verdict: Verdict }
  | { type: 'RESET' }

export interface DealOut {
  phase_1: CardOut[]
  phase_2: CardOut[]
  phase_3: CardOut[]
}

// API response shapes (snake_case from backend)
export interface CardOut {
  id: number
  prompt_text: string
  response_text: string
  harm_category: string
  phase: number
  generation_tier: number
  is_harmful: boolean
  gork_verdict: boolean | null
  gork_confidence: number | null
  gork_reasoning: string | null
  agent_condition: AgentCondition
}

export interface SessionCreated {
  session_id: number
  share_id: string
}

export interface SessionResult {
  share_id: string
  total_days: number | null
  total_decisions: number | null
  accuracy: number | null
  game_over_condition: string | null
  phase_reached: number | null
  agreement_rate: number | null
  calibration_accuracy: number | null
  total_escalated: number | null
}

export interface BatchAccepted {
  accepted: number
}

export interface AnalyticsSummary {
  total_sessions: number
  sessions_today: number
  global_fp_rate: number
  global_fn_rate: number
  avg_latency_ms: number
  phase_survival: Record<string, number>
  system_drift_error_rate: Array<{ date: string; error_rate: number }>
  escalation_rate: number
  escalation_rate_by_category: Record<string, number>
}
