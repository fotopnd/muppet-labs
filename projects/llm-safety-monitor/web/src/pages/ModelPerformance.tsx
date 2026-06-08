import { useState } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useCalibration, useModelMetrics, useMetricsTimeseries } from '@/api/metrics'
import { ErrorMessage } from '@/components/ErrorMessage'
import { MetricComparisonChart } from '@/components/MetricComparisonChart'
import { Skeleton } from '@/components/Skeleton'
import type { ModelCalibration, SourceDatasetFilter } from '@/types'

const SOURCE_OPTIONS: { value: SourceDatasetFilter; label: string }[] = [
  { value: 'wildguard', label: 'WildGuard' },
  { value: 'all', label: 'All sources' },
]

const MODEL_COLORS: Record<string, string> = {
  pair_classifier: '#2563eb',
  prompt_detector: '#059669',
  taxonomy_classifier: '#f59e0b',
}
const FALLBACK_COLORS = ['#2563eb', '#059669', '#f59e0b', '#dc2626', '#7c3aed']

function CalibrationChart({ model }: { model: ModelCalibration }) {
  const color = MODEL_COLORS[model.model_name] ?? FALLBACK_COLORS[0]
  const data = model.bins.map((b) => ({
    midpoint: Math.round(((b.bin_lower + b.bin_upper) / 2) * 100) / 100,
    actual: b.actual_positive_rate,
    count: b.count,
  }))

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5">
      <h3 className="font-sans text-sm font-semibold text-slate-900 mb-1">
        {model.model_name} — calibration
      </h3>
      <p className="text-xs text-slate-400 mb-3">
        Confidence vs actual positive rate. Diagonal = perfect calibration.
      </p>
      <div className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="midpoint"
              type="number"
              domain={[0, 1]}
              tick={{ fontSize: 10 }}
              tickCount={5}
              label={{ value: 'Confidence', position: 'insideBottom', offset: -2, fontSize: 10 }}
            />
            <YAxis
              dataKey="actual"
              type="number"
              domain={[0, 1]}
              tick={{ fontSize: 10 }}
              tickCount={5}
              label={{ value: 'Actual +rate', angle: -90, position: 'insideLeft', fontSize: 10 }}
            />
            <Tooltip
              formatter={(v: number, name: string) =>
                name === 'count' ? v : v.toFixed(3)
              }
            />
            {/* Perfect calibration reference line */}
            <ReferenceLine
              segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]}
              stroke="#cbd5e1"
              strokeDasharray="4 4"
            />
            <Scatter data={data} fill={color} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export function ModelPerformance() {
  const [source, setSource] = useState<SourceDatasetFilter>('wildguard')

  const { data: metricsData, isLoading: metricsLoading, isError: metricsError } = useModelMetrics(source)
  const { data: tsData, isLoading: tsLoading, isError: tsError } = useMetricsTimeseries(source)
  const { data: calData, isLoading: calLoading, isError: calError } = useCalibration(source)

  if (metricsLoading || tsLoading || calLoading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-8 w-48" />
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-52 w-full" />
        ))}
      </div>
    )
  }

  if (metricsError || tsError || calError) {
    return <ErrorMessage message="Failed to load model metrics" />
  }

  const models = metricsData?.models ?? []
  const tsModels = tsData?.models ?? []
  const calModels = calData?.models ?? []
  const fmt = (v: number) => (v * 100).toFixed(1) + '%'

  return (
    <div className="flex flex-col gap-4">
      {/* Source filter */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-500">Evaluate against:</span>
        <div className="flex gap-1">
          {SOURCE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setSource(opt.value)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                source === opt.value
                  ? 'bg-slate-900 text-white'
                  : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        {source === 'all' && (
          <span className="text-xs text-amber-600">
            ⚠ Includes noisy HH-RLHF labels — F1 will appear inflated
          </span>
        )}
      </div>

      {/* Summary table */}
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

      {/* Performance timeseries */}
      <MetricComparisonChart title="F1 by Model" metric="f1" models={tsModels} />
      <MetricComparisonChart title="Precision by Model" metric="precision" models={tsModels} />
      <MetricComparisonChart title="Recall by Model" metric="recall" models={tsModels} />

      {/* Calibration reliability diagrams */}
      {calModels.length > 0 && (
        <>
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mt-2">
            Calibration
          </h2>
          {calModels.map((m) => (
            <CalibrationChart key={m.model_name} model={m} />
          ))}
        </>
      )}

      {models.length === 0 && (
        <p className="text-center text-slate-400 py-12 text-sm">
          No events with ground-truth labels yet.
        </p>
      )}
    </div>
  )
}
