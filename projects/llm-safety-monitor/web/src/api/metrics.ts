import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/api/client'
import type { CalibrationResponse, DisagreementsResponse, MetricsResponse } from '@/types'

export function useModelMetrics() {
  return useQuery<MetricsResponse>({
    queryKey: ['metrics'],
    queryFn: () => apiFetch<MetricsResponse>('/metrics'),
    refetchInterval: 30_000,
  })
}

export function useCalibration() {
  return useQuery<CalibrationResponse>({
    queryKey: ['metrics', 'calibration'],
    queryFn: () => apiFetch<CalibrationResponse>('/metrics/calibration'),
    refetchInterval: 60_000,
  })
}

export function useDisagreements() {
  return useQuery<DisagreementsResponse>({
    queryKey: ['metrics', 'disagreements'],
    queryFn: () => apiFetch<DisagreementsResponse>('/metrics/disagreements'),
    refetchInterval: 30_000,
  })
}
