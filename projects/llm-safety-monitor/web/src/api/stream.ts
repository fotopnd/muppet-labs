import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/api/client'
import type { StreamResponse } from '@/types'

export function useRecentEvents(limit = 50) {
  return useQuery<StreamResponse>({
    queryKey: ['stream', 'recent', limit],
    queryFn: () => apiFetch<StreamResponse>(`/stream/recent?limit=${limit}`),
    refetchInterval: 5000,
  })
}
