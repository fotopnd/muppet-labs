export type Verdict = 'CLEAR' | 'REDACT' | 'ESCALATE'
export type AgentCondition = 'none' | 'tier_1' | 'tier_2' | 'tier_3'
export type GameOverReason =
  | 'TRUST_ZERO'
  | 'SECURITY_MAX'
  | 'TREASURY_ZERO'
  | 'LEGITIMACY_ZERO'
  | 'COMPLIANCE_MAX'
  | 'COMPLIANCE_ZERO'

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
  sovereignVerdict: boolean | null
  sovereignConfidence: number | null
  sovereignReasoning: string | null
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
  isCalibration: boolean
}

export interface CategoryAccuracy {
  correct: number
  total: number
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
  categoryTiers: Record<string, 1 | 2 | 3>
  categoryAccuracy: Record<string, CategoryAccuracy>
  upgradePending: string | null
  dayCorrect: number
  dayEscalated: number
  totalDecisions: number
  totalCorrect: number
  totalEscalated: number
  isCalibration: boolean
}

export type GameAction =
  | { type: 'START_SESSION'; sessionId: number; calibrationCards: Card[] }
  | { type: 'SWIPE'; verdict: Verdict }
  | { type: 'DAY_ACKNOWLEDGED' }
  | { type: 'PHASE_CARDS_LOADED'; cards: Card[] }
  | { type: 'UPGRADE_ACKNOWLEDGED'; category: string }
  | { type: 'RESET' }

// API response shapes (snake_case from backend)
export interface CardOut {
  id: number
  document_text: string
  harm_category: string
  phase: number
  generation_tier: number
  is_harmful: boolean
  sovereign_verdict: boolean | null
  sovereign_confidence: number | null
  sovereign_reasoning: string | null
  agent_condition: AgentCondition
}

export interface SessionCreated {
  session_id: number
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
