import { useQuery } from '@tanstack/react-query'

import { apiFetch } from '@/api/client'
import type { ExperimentSummary } from '@/types'

export function useExperiments() {
  return useQuery({
    queryKey: ['experiments'],
    queryFn: () => apiFetch<ExperimentSummary[]>('/experiments'),
  })
}
