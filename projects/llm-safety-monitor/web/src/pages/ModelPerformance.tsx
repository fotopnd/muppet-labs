import { useModelMetrics } from '@/api/metrics'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Skeleton } from '@/components/Skeleton'
import type { ModelMetrics } from '@/types'

function MetricRow({ model }: { model: ModelMetrics }) {
  return (
    <tr className="border-b border-gray-100">
      <td className="py-2 pr-4 font-mono text-sm text-gray-700">{model.model_name}</td>
      <td className="py-2 pr-4 text-center font-medium">{(model.f1 * 100).toFixed(1)}%</td>
      <td className="py-2 pr-4 text-center">{(model.precision * 100).toFixed(1)}%</td>
      <td className="py-2 pr-4 text-center">{(model.recall * 100).toFixed(1)}%</td>
      <td className="py-2 text-center text-gray-500 text-sm">{model.sample_count.toLocaleString()}</td>
    </tr>
  )
}

export function ModelPerformance() {
  const { data, isLoading, isError } = useModelMetrics()

  if (isLoading) return <Skeleton className="h-40 w-full" />
  if (isError) return <ErrorMessage message="Failed to load model metrics" />

  const models = data?.models ?? []

  return (
    <div>
      <p className="text-sm text-gray-500 mb-4">
        F1, precision, and recall computed against live-stream events with known ground-truth labels.
      </p>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-500 text-xs uppercase border-b border-gray-200">
            <th className="pb-2 pr-4">Model</th>
            <th className="pb-2 pr-4 text-center">F1</th>
            <th className="pb-2 pr-4 text-center">Precision</th>
            <th className="pb-2 pr-4 text-center">Recall</th>
            <th className="pb-2 text-center">Samples</th>
          </tr>
        </thead>
        <tbody>
          {models.map((m) => (
            <MetricRow key={m.model_name} model={m} />
          ))}
        </tbody>
      </table>
      {models.length === 0 && (
        <p className="text-center text-gray-400 py-12">No events with ground-truth labels yet.</p>
      )}
    </div>
  )
}
