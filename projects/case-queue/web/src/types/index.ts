export type CaseCategory =
  | 'toxic'
  | 'severe_toxic'
  | 'obscene'
  | 'threat'
  | 'insult'
  | 'identity_hate'

export type Severity = 'low' | 'medium' | 'high'
export type CaseStatus = 'pending' | 'approved' | 'rejected' | 'escalated'
export type Action = 'approve' | 'reject' | 'escalate'
export type ActorRole = 'reviewer' | 'senior_reviewer'

export interface Decision {
  id: string
  actor_id: string
  actor_role: ActorRole
  action: Action
  notes: string
  created_at: string
}

export interface CaseListItem {
  id: string
  category: CaseCategory
  severity: Severity
  status: CaseStatus
  created_at: string
}

export interface CaseDetail {
  id: string
  content: string
  category: CaseCategory
  severity: Severity
  status: CaseStatus
  source: string
  meta: Record<string, unknown>
  created_at: string
  updated_at: string
  decisions: Decision[]
}

export interface AuditEntry {
  id: string
  case_id: string
  actor_id: string
  actor_role: ActorRole
  action: Action
  notes: string
  created_at: string
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface DecisionCreate {
  action: Action
  notes: string
}

export type CaseSortBy = 'created_at' | 'severity' | 'category' | 'status'
export type AuditSortBy = 'created_at' | 'action' | 'actor_id'
export type SortDir = 'asc' | 'desc'

export interface CaseFilters {
  page?: number
  page_size?: number
  category?: CaseCategory
  severity?: Severity
  status?: CaseStatus
  date_from?: string
  date_to?: string
  sort_by?: CaseSortBy
  sort_dir?: SortDir
}

export interface AuditFilters {
  page?: number
  page_size?: number
  case_id?: string
  actor_id?: string
  action?: Action
  date_from?: string
  date_to?: string
  sort_by?: AuditSortBy
  sort_dir?: SortDir
}
