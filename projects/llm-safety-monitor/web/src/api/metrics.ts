import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/api/client'
import type { MetricsResponse, TaxonomyTimeseriesResponse, TimeseriesResponse } from '@/types'

export function useModelMetrics() {
  return useQuery<MetricsResponse>({
    queryKey: ['metrics'],
    queryFn: () => apiFetch<MetricsResponse>('/metrics'),
    refetchInterval: 30_000,
  })
}

export function useMetricsTimeseries() {
  return useQuery<TimeseriesResponse>({
    queryKey: ['metrics', 'timeseries'],
    queryFn: () => apiFetch<TimeseriesResponse>('/metrics/timeseries?bucket_minutes=5'),
    refetchInterval: 30_000,
  })
}

export function useTaxonomyTimeseries() {
  return useQuery<TaxonomyTimeseriesResponse>({
    queryKey: ['metrics', 'taxonomy', 'timeseries'],
    queryFn: () => apiFetch<TaxonomyTimeseriesResponse>('/metrics/taxonomy/timeseries?bucket_minutes=5'),
    refetchInterval: 30_000,
  })
}
