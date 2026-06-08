import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/api/client'
import type {
  CalibrationResponse,
  EscalationQueueResponse,
  MetricsResponse,
  SourceDatasetFilter,
  TaxonomyTimeseriesResponse,
  TimeseriesResponse,
} from '@/types'

export function useModelMetrics(sourceDataset: SourceDatasetFilter = 'wildguard') {
  return useQuery<MetricsResponse>({
    queryKey: ['metrics', sourceDataset],
    queryFn: () => apiFetch<MetricsResponse>(`/metrics?source_dataset=${sourceDataset}`),
    refetchInterval: 30_000,
  })
}

export function useMetricsTimeseries(sourceDataset: SourceDatasetFilter = 'wildguard') {
  return useQuery<TimeseriesResponse>({
    queryKey: ['metrics', 'timeseries', sourceDataset],
    queryFn: () =>
      apiFetch<TimeseriesResponse>(
        `/metrics/timeseries?bucket_minutes=5&source_dataset=${sourceDataset}`,
      ),
    refetchInterval: 30_000,
  })
}

export function useCalibration(sourceDataset: SourceDatasetFilter = 'wildguard') {
  return useQuery<CalibrationResponse>({
    queryKey: ['metrics', 'calibration', sourceDataset],
    queryFn: () =>
      apiFetch<CalibrationResponse>(`/metrics/calibration?source_dataset=${sourceDataset}`),
    refetchInterval: 60_000,
  })
}

export function useDisagreements(sourceDataset: SourceDatasetFilter = 'wildguard') {
  return useQuery<EscalationQueueResponse>({
    queryKey: ['metrics', 'disagreements', sourceDataset],
    queryFn: () =>
      apiFetch<EscalationQueueResponse>(
        `/metrics/disagreements?source_dataset=${sourceDataset}`,
      ),
    refetchInterval: 30_000,
  })
}

export function useTaxonomyTimeseries() {
  return useQuery<TaxonomyTimeseriesResponse>({
    queryKey: ['metrics', 'taxonomy', 'timeseries'],
    queryFn: () =>
      apiFetch<TaxonomyTimeseriesResponse>('/metrics/taxonomy/timeseries?bucket_minutes=5'),
    refetchInterval: 30_000,
  })
}
