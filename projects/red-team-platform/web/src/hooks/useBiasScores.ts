import { useQuery } from '@tanstack/react-query'
import type { BiasScoresOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export function useBiasScores() {
  return useQuery<BiasScoresOut>({
    queryKey: ['bias-scores'],
    queryFn: () => fetch(`${API}/bias/scores`).then((r) => r.json()),
    refetchInterval: 60_000,
  })
}
