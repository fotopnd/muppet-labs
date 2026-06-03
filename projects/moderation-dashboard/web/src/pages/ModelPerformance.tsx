import { ErrorMessage } from '@/components/ErrorMessage'
import { ModelCard } from '@/components/ModelCard'
import { ModelCardSkeleton } from '@/components/ModelCardSkeleton'
import { useProductionMetrics } from '@/api/production'

export function ModelPerformance() {
  const { metrics, history, isLoading, isError } = useProductionMetrics()

  if (isError) {
    return <ErrorMessage title="Failed to load production metrics" body="Retrying automatically…" />
  }

  if (isLoading || !metrics) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {[0, 1, 2, 3, 4].map(i => (
          <ModelCardSkeleton key={i} />
        ))}
      </div>
    )
  }

  return (
    <div>
      <h2 className="font-interface text-base font-semibold text-text-intense mb-4">
        Production Group — Round-Robin Routing
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {metrics.map(m => (
          <ModelCard
            key={m.model_name}
            metrics={m}
            sparklineData={history[m.model_name] ?? []}
          />
        ))}
      </div>
    </div>
  )
}
