import { useQuery } from '@tanstack/react-query'
import type { SampleOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export function useSample(runId: string | null) {
  return useQuery<SampleOut>({
    queryKey: ['sample', runId],
    queryFn: () => fetch(`${API}/sample/${runId}`).then((r) => r.json()),
    enabled: runId !== null,
  })
}
