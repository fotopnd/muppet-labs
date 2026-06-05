import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch, apiPost } from './client'
import type { CaseDecisionCreate, CaseDecisionRead, EscalationCase } from '@/types'

export function useCases() {
  return useQuery({
    queryKey: ['cases'],
    queryFn: () => apiFetch<EscalationCase[]>('/cases'),
    refetchInterval: 15000,
  })
}

export function useCreateDecision() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ escalationId, body }: { escalationId: string; body: CaseDecisionCreate }) =>
      apiPost<CaseDecisionRead>(`/cases/${escalationId}/decide`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cases'] })
    },
  })
}
