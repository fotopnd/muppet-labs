import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiFetch } from './client'
import type {
  CaseDetail,
  CaseFilters,
  CaseListItem,
  Decision,
  DecisionCreate,
  Page,
} from '@/types'

function toCaseParams(filters: CaseFilters): string {
  const params = new URLSearchParams()
  if (filters.page !== undefined) params.set('page', String(filters.page))
  if (filters.page_size !== undefined) params.set('page_size', String(filters.page_size))
  if (filters.category) params.set('category', filters.category)
  if (filters.severity) params.set('severity', filters.severity)
  if (filters.status) params.set('status', filters.status)
  if (filters.date_from) params.set('date_from', filters.date_from)
  if (filters.date_to) params.set('date_to', filters.date_to)
  return params.toString()
}

export function useCases(filters: CaseFilters) {
  return useQuery({
    queryKey: ['cases', filters],
    queryFn: () => apiFetch<Page<CaseListItem>>(`/cases?${toCaseParams(filters)}`),
  })
}

export function useCase(id: string) {
  return useQuery({
    queryKey: ['cases', id],
    queryFn: () => apiFetch<CaseDetail>(`/cases/${id}`),
    enabled: Boolean(id),
  })
}

export function useCreateDecision(caseId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: DecisionCreate) =>
      apiFetch<Decision>(`/cases/${caseId}/decisions`, {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cases'] })
      queryClient.invalidateQueries({ queryKey: ['audit-log'] })
    },
  })
}
