import { useQuery } from '@tanstack/react-query'
import type { RegressionOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export function useRegression() {
  return useQuery<RegressionOut>({
    queryKey: ['regression'],
    queryFn: () => fetch(`${API}/regression`).then((r) => r.json()),
    refetchInterval: 30_000,
  })
}
