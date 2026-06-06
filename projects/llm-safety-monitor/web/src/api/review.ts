import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/api/client'
import type { DisagreementsResponse } from '@/types'

export function useEscalationQueue() {
  return useQuery<DisagreementsResponse>({
    queryKey: ['cases'],
    queryFn: () => apiFetch<DisagreementsResponse>('/cases'),
    refetchInterval: 10_000,
  })
}
