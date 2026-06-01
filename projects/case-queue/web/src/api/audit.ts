import { useQuery } from '@tanstack/react-query'

import { apiFetch } from './client'
import type { AuditEntry, AuditFilters, Page } from '@/types'

function toAuditParams(filters: AuditFilters): string {
  const params = new URLSearchParams()
  if (filters.page !== undefined) params.set('page', String(filters.page))
  if (filters.page_size !== undefined) params.set('page_size', String(filters.page_size))
  if (filters.case_id) params.set('case_id', filters.case_id)
  if (filters.actor_id) params.set('actor_id', filters.actor_id)
  if (filters.action) params.set('action', filters.action)
  if (filters.date_from) params.set('date_from', filters.date_from)
  if (filters.date_to) params.set('date_to', filters.date_to)
  return params.toString()
}

export function useAuditLog(filters: AuditFilters) {
  return useQuery({
    queryKey: ['audit-log', filters],
    queryFn: () => apiFetch<Page<AuditEntry>>(`/audit-log?${toAuditParams(filters)}`),
  })
}
