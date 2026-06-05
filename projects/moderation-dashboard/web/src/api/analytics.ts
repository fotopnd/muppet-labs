import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch, apiPost } from './client'
import type { AnalyticsResponse } from '@/types'

export function useAnalytics() {
  return useQuery({
    queryKey: ['metrics', 'analytics'],
    queryFn: () => apiFetch<AnalyticsResponse>('/metrics/analytics'),
    refetchInterval: 60000,
  })
}

export function useRestart() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => apiPost<void>('/admin/restart'),
    onSuccess: () => {
      queryClient.invalidateQueries()
    },
  })
}
