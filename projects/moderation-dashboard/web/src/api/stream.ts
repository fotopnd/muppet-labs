import { useQuery } from '@tanstack/react-query'
import { apiFetch } from './client'
import type { AnomalyFlag, StreamMetrics, StreamTimeSeriesPoint } from '@/types'

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

export function useStreamTimeSeries() {
  return useQuery({
    queryKey: ['metrics', 'stream', 'timeseries'],
    queryFn: () => apiFetch<StreamTimeSeriesPoint[]>('/metrics/stream/timeseries'),
    refetchInterval: 30000,
  })
}
