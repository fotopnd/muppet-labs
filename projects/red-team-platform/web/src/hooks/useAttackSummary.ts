import { useQuery } from '@tanstack/react-query'
import type { AttackSummaryOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

type Filters = {
  source?: string | null
  harm_category?: string | null
  strategy?: string | null
}

export function useAttackSummary(filters: Filters = {}) {
  const query = new URLSearchParams()
  if (filters.source) query.set('source', filters.source)
  if (filters.harm_category) query.set('harm_category', filters.harm_category)
  if (filters.strategy) query.set('strategy', filters.strategy)

  return useQuery<AttackSummaryOut>({
    queryKey: ['attack-summary', filters],
    queryFn: () => fetch(`${API}/attacks/summary?${query}`).then((r) => r.json()),
    staleTime: 0,
  })
}
