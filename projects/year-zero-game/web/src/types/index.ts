export type Verdict = 'CLEAR' | 'REDACT' | 'ESCALATE'
export type AgentCondition = 'none' | 'tier_1' | 'tier_2' | 'tier_3'
export type GameOverReason =
  | 'TRUST_ZERO'
  | 'SECURITY_MAX'
  | 'TREASURY_ZERO'
  | 'LEGITIMACY_ZERO'
  | 'COMPLIANCE_MAX'
  | 'DAYS_COMPLETE'

export interface BarState {
  publicTrust: number
  security: number
  treasury: number
  legitimacy: number
  compliance: number
}

export interface Card {
  id: number
  documentText: string
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
  bars: BarState
  gameDay: number
  phase: number
  categoryTier: number
}

export type GamePhase =
  | 'start'
  | 'lore'
  | 'playing'
  | 'day_end'
  | 'upgrade'
  | 'game_over'

export interface GameState {
  phase: GamePhase
  sessionId: number | null
  gameDay: number
  cardsInDay: number
  cardStartedAt: number | null
  currentCard: Card | null
  cardPool: Card[]
  pendingDecisions: PendingDecision[]
  bars: BarState
  activePhase: 1 | 2 | 3
  gameOverReason: GameOverReason | null
  dayCorrect: number
  dayEscalated: number
  totalDecisions: number
  totalCorrect: number
  totalEscalated: number
  phaseCardsMap: Record<1 | 2 | 3, Card[]>
}

export type GameAction =
  | { type: 'START_SESSION'; sessionId: number; phaseCards: Record<1 | 2 | 3, Card[]> }
  | { type: 'SWIPE'; verdict: Verdict }
  | { type: 'DAY_ACKNOWLEDGED' }
  | { type: 'RESET' }

export interface DealOut {
  phase_1: CardOut[]
  phase_2: CardOut[]
  phase_3: CardOut[]
}

// API response shapes (snake_case from backend)
export interface CardOut {
  id: number
  document_text: string
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
