import { useQuery } from '@tanstack/react-query'
import type { Session } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export function useSessions() {
  return useQuery<Session[]>({
    queryKey: ['sessions'],
    queryFn: () => fetch(`${API}/sessions`).then((r) => r.json()),
    refetchInterval: 30_000,
  })
}
