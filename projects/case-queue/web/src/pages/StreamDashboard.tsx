import { useEffect, useState } from 'react'

import { useStreamMetrics } from '@/api/stream'
import { ErrorMessage } from '@/components/ErrorMessage'
import { ModelMetricsCard } from '@/components/ModelMetricsCard'
import type { HistoryPoint } from '@/types/stream'

const MAX_HISTORY = 30

function CardSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-3 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="h-4 bg-muted rounded w-32" />
        <div className="h-5 bg-muted rounded w-16" />
      </div>
      <div className="space-y-2">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-3 bg-muted rounded" />
        ))}
      </div>
    </div>
  )
}

export function StreamDashboard() {
  const { data, isLoading, error } = useStreamMetrics()
  const [history, setHistory] = useState<Record<string, HistoryPoint[]>>({})

  useEffect(() => {
    if (!data) return
    const t = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    setHistory(prev => {
      const next = { ...prev }
      for (const m of data.models) {
        if (m.status !== 'active') continue
        const point: HistoryPoint = {
          t,
          accuracy: m.accuracy,
          p50: m.p50_latency_ms,
          p95: m.p95_latency_ms,
          throughput: m.throughput_cps,
        }
        const existing = prev[m.model_name] ?? []
        next[m.model_name] = [...existing, point].slice(-MAX_HISTORY)
      }
      return next
    })
  }, [data])

  return (
    <>
      <div className="border-b border-border px-6 py-5 flex items-center justify-between bg-card">
        <h1 className="text-xl font-semibold text-foreground font-interface">
          Model Comparison
        </h1>
        {data && (
          <p className="text-sm text-muted-foreground font-data">
            Updated {new Date(data.generated_at).toLocaleTimeString()}
          </p>
        )}
      </div>

      <div className="px-6 py-6">
        {error && !data && (
          <ErrorMessage message="Could not connect to stream metrics API" />
        )}

        {isLoading && !data && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {[...Array(5)].map((_, i) => <CardSkeleton key={i} />)}
          </div>
        )}

        {data && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {data.models.map(m => (
              <ModelMetricsCard
                key={m.model_name}
                metrics={m}
                history={history[m.model_name] ?? []}
              />
            ))}
          </div>
        )}
      </div>
    </>
  )
}
