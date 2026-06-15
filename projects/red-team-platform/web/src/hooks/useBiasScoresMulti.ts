import { useQuery } from '@tanstack/react-query'
import type { BiasMultiModelOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export function useBiasScoresMulti() {
  return useQuery<BiasMultiModelOut>({
    queryKey: ['biasScoresMulti'],
    queryFn: () => fetch(`${API}/bias/scores/multi`).then((r) => r.json()),
    staleTime: 60_000,
  })
}
