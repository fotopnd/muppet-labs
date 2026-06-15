import { useQuery } from '@tanstack/react-query'
import type { TriageSummaryOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export function useTriageSummary() {
  return useQuery<TriageSummaryOut>({
    queryKey: ['triage-summary'],
    queryFn: () => fetch(`${API}/runs/triage-summary`).then((r) => r.json()),
    staleTime: 30_000,
  })
}
