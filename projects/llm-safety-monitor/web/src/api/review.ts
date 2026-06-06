import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch, apiPost } from '@/api/client'
import type { EscalationQueueResponse, ReviewDecisionResponse } from '@/types'

export function useEscalationQueue() {
  return useQuery<EscalationQueueResponse>({
    queryKey: ['cases'],
    queryFn: () => apiFetch<EscalationQueueResponse>('/cases'),
    refetchInterval: 10_000,
  })
}

export function useDecide() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ caseId, decision }: { caseId: string; decision: string }) =>
      apiPost<ReviewDecisionResponse>(`/cases/${caseId}/decide`, { decision }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['cases'] })
    },
  })
}
