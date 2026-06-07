import { useQuery } from '@tanstack/react-query'

import { apiFetch } from '@/api/client'
import type { ExperimentResults } from '@/types'

export function useResults(experimentId: number | null) {
  return useQuery({
    queryKey: ['results', experimentId],
    queryFn: () => apiFetch<ExperimentResults>(`/results/${experimentId}`),
    enabled: experimentId !== null,
    refetchInterval: (query) => (query.state.data?.uplift === null ? 30_000 : false),
  })
}
