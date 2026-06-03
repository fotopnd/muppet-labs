import { useQuery } from '@tanstack/react-query'
import { apiFetch } from './client'
import type { AnomalyFlag, StreamMetrics } from '@/types'

export function useStreamMetrics() {
  return useQuery({
    queryKey: ['metrics', 'stream'],
    queryFn: () => apiFetch<StreamMetrics>('/metrics/stream'),
    refetchInterval: 5000,
  })
}

export function useAnomalyFlags() {
  return useQuery({
    queryKey: ['metrics', 'anomalies'],
    queryFn: () => apiFetch<AnomalyFlag[]>('/metrics/anomalies'),
    refetchInterval: 10000,
  })
}
