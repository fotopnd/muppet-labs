import { useQuery } from '@tanstack/react-query'
import type { TopFailuresOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export function useTopFailures(limit = 20) {
  return useQuery<TopFailuresOut>({
    queryKey: ['topFailures', limit],
    queryFn: () => fetch(`${API}/top-failures?limit=${limit}`).then((r) => r.json()),
    staleTime: 60_000,
  })
}
