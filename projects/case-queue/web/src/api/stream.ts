import { useQuery, type UseQueryResult } from '@tanstack/react-query'

import type { MetricsResponse } from '@/types/stream'

const STREAM_API_BASE = import.meta.env['VITE_STREAM_API_URL'] ?? 'http://localhost:8001'

async function fetchMetrics(): Promise<MetricsResponse> {
  const res = await fetch(`${STREAM_API_BASE}/metrics`)
  if (!res.ok) throw new Error(`Metrics API error: ${res.status}`)
  return res.json() as Promise<MetricsResponse>
}

export function useStreamMetrics(): UseQueryResult<MetricsResponse, Error> {
  return useQuery({
    queryKey: ['stream-metrics'],
    queryFn: fetchMetrics,
    refetchInterval: 3000,
    retry: 2,
  })
}
