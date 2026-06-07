import { useQuery } from '@tanstack/react-query'
import type { StrategyComparisonOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export function useStrategyComparison() {
  return useQuery<StrategyComparisonOut>({
    queryKey: ['strategyComparison'],
    queryFn: () => fetch(`${API}/strategy-comparison`).then((r) => r.json()),
    refetchInterval: 30_000,
  })
}
