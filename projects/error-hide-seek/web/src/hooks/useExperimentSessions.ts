import { useQuery } from '@tanstack/react-query'

import { apiFetch } from '@/api/client'
import type { SessionListItem } from '@/types'

export function useExperimentSessions(experimentId: number | null) {
  return useQuery({
    queryKey: ['experiment-sessions', experimentId],
    queryFn: () => apiFetch<SessionListItem[]>(`/experiments/${experimentId}/sessions`),
    enabled: experimentId !== null,
    staleTime: 30_000,
  })
}
