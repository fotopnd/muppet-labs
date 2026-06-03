import { useQuery } from '@tanstack/react-query'
import { apiFetch, externalFetch } from './client'
import type { AnalyticsResponse, CasePage } from '@/types'

const CASE_QUEUE_URL = import.meta.env.VITE_CASE_QUEUE_URL ?? 'http://localhost:8000'

export function useAnalytics() {
  return useQuery({
    queryKey: ['metrics', 'analytics'],
    queryFn: () => apiFetch<AnalyticsResponse>('/metrics/analytics'),
    refetchInterval: 60000,
  })
}

export function useDashboardCases() {
  return useQuery({
    queryKey: ['case-queue', 'dashboard-cases'],
    queryFn: () =>
      externalFetch<CasePage>(
        `${CASE_QUEUE_URL}/cases?source=moderation-dashboard&status=pending&page_size=50`,
      ),
    refetchInterval: 15000,
  })
}
