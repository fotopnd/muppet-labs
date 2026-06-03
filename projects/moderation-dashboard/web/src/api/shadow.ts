import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiFetch } from './client'
import type { ModelMetrics } from '@/types'

const MAX_HISTORY = 30

export function useShadowMetrics() {
  const [history, setHistory] = useState<Record<string, number[]>>({})

  const query = useQuery({
    queryKey: ['metrics', 'shadow'],
    queryFn: () => apiFetch<ModelMetrics[]>('/metrics/shadow'),
    refetchInterval: 3000,
  })

  useEffect(() => {
    if (!query.data) return
    setHistory(prev => {
      const next = { ...prev }
      for (const m of query.data!) {
        const pts = next[m.model_name] ?? []
        next[m.model_name] = [...pts, m.f1 ?? 0].slice(-MAX_HISTORY)
      }
      return next
    })
  }, [query.data])

  return {
    metrics: query.data,
    history,
    isLoading: query.isLoading,
    isError: query.isError,
  }
}
