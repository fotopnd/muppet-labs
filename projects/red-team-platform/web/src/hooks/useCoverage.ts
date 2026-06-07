import { useQuery } from '@tanstack/react-query'
import type { CoverageOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export function useCoverage() {
  return useQuery<CoverageOut>({
    queryKey: ['coverage'],
    queryFn: () => fetch(`${API}/coverage`).then((r) => r.json()),
    refetchInterval: 30_000,
  })
}
