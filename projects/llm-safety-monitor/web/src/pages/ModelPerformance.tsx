import { useModelMetrics, useMetricsTimeseries } from '@/api/metrics'
import { ErrorMessage } from '@/components/ErrorMessage'
import { MetricComparisonChart } from '@/components/MetricComparisonChart'
import { Skeleton } from '@/components/Skeleton'

export function ModelPerformance() {
  const { data: metricsData, isLoading: metricsLoading, isError: metricsError } = useModelMetrics()
  const { data: tsData, isLoading: tsLoading, isError: tsError } = useMetricsTimeseries()

  if (metricsLoading || tsLoading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-12 w-full" />
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-52 w-full" />
        ))}
      </div>
    )
  }

  if (metricsError || tsError) {
    return <ErrorMessage message="Failed to load model metrics" />
  }

  const models = metricsData?.models ?? []
  const tsModels = tsData?.models ?? []
  const fmt = (v: number) => (v * 100).toFixed(1) + '%'

  return (
    <div className="flex flex-col gap-4">
      {/* Compact current-values summary */}
      {models.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-slate-400 text-xs uppercase tracking-wide">
                <th className="px-4 py-2">Model</th>
                <th className="px-4 py-2 text-right">F1</th>
                <th className="px-4 py-2 text-right">Precision</th>
                <th className="px-4 py-2 text-right">Recall</th>
                <th className="px-4 py-2 text-right text-slate-300">n</th>
              </tr>
            </thead>
            <tbody>
              {models.map((m) => (
                <tr key={m.model_name} className="border-b border-slate-50 last:border-0">
                  <td className="px-4 py-2 font-mono text-xs text-slate-700">{m.model_name}</td>
                  <td className="px-4 py-2 font-mono text-xs text-right text-slate-900">{fmt(m.f1)}</td>
                  <td className="px-4 py-2 font-mono text-xs text-right text-slate-900">{fmt(m.precision)}</td>
                  <td className="px-4 py-2 font-mono text-xs text-right text-slate-900">{fmt(m.recall)}</td>
                  <td className="px-4 py-2 font-mono text-xs text-right text-slate-400">{m.sample_count.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Three timeseries charts — one per metric, all models as lines */}
      <MetricComparisonChart title="F1 by Model" metric="f1" models={tsModels} />
      <MetricComparisonChart title="Precision by Model" metric="precision" models={tsModels} />
      <MetricComparisonChart title="Recall by Model" metric="recall" models={tsModels} />

      {models.length === 0 && (
        <p className="text-center text-slate-400 py-12 text-sm">
          No events with ground-truth labels yet.
        </p>
      )}
    </div>
  )
}
