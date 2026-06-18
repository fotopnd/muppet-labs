import { useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useCalibration, useModelMetrics, useMetricsTimeseries } from '@/api/metrics'
import { ErrorMessage } from '@/components/ErrorMessage'
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

const MODEL_DISPLAY: Record<string, string> = {
  pair_classifier: 'Pair Classifier',
  prompt_detector: 'Prompt Detector',
  taxonomy_classifier: 'Taxonomy Classifier',
}

const MODEL_ROLE: Record<string, string> = {
  pair_classifier:
    'Conservative catch-all. Evaluates full prompt+response pairs for harmful compliance. ' +
    'Trained on WildGuard — 87.5% F1 at 0.5 threshold. Lowest latency of the three.',
  prompt_detector:
    'First-pass filter. Scores prompt-level intent without waiting for a response. ' +
    'Useful for real-time blocking; 89.2% F1. Highest precision (fewer false positives).',
  taxonomy_classifier:
    'Labels flagged content into 13 WildGuard harm categories (physical safety, ' +
    'social stereotypes, etc.). Only invoked after pair_classifier flags a request.',
}

const FALLBACK_COLORS = ['#2563eb', '#059669', '#f59e0b', '#dc2626', '#7c3aed']

function CalibrationChart({ model }: { model: ModelCalibration }) {
  const color = MODEL_COLORS[model.model_name] ?? FALLBACK_COLORS[0]
  const data = model.bins
    .filter((b) => b.count > 0)
    .map((b) => ({
      x: Math.round(((b.bin_lower + b.bin_upper) / 2) * 100) / 100,
      y: b.actual_positive_rate,
      count: b.count,
    }))

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5">
      <h3 className="font-sans text-sm font-semibold text-slate-900 mb-0.5">
        {MODEL_DISPLAY[model.model_name] ?? model.model_name} — calibration
      </h3>
      <p className="text-xs text-slate-400 mb-3">
        Predicted confidence vs actual positive rate. Dashed diagonal = perfect calibration.
        Dot size ∝ √sample count.
      </p>
      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 16, bottom: 24, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="x"
              type="number"
              domain={[0, 1]}
              tick={{ fontSize: 10 }}
              tickCount={6}
              label={{ value: 'Predicted confidence', position: 'insideBottom', offset: -14, fontSize: 10 }}
            />
            <YAxis
              dataKey="y"
              type="number"
              domain={[0, 1]}
              tick={{ fontSize: 10 }}
              tickCount={6}
              label={{ value: 'Actual +rate', angle: -90, position: 'insideLeft', offset: 8, fontSize: 10 }}
            />
            <Tooltip
              formatter={((v: any, name: any) => String(name) === 'y' ? [(v as number).toFixed(3), 'Actual +rate'] : [v, String(name)]) as any}
            />
            <ReferenceLine
              segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]}
              stroke="#cbd5e1"
              strokeDasharray="4 4"
            />
            <Line
              type="monotone"
              dataKey="y"
              stroke={color}
              strokeWidth={1.5}
              dot={(props: any) => {
                const r = Math.max(5, Math.min(18, Math.sqrt(props.payload.count) / 12))
                return <circle key={`dot-${props.index}`} cx={props.cx} cy={props.cy} r={r} fill={color} fillOpacity={0.85} stroke="white" strokeWidth={1.5} />
              }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export function ModelPerformance() {
  const [source, setSource] = useState<SourceDatasetFilter>('wildguard')

  const { data: metricsData, isLoading: metricsLoading, isError: metricsError } = useModelMetrics(source)
  const { data: tsData, isLoading: tsLoading } = useMetricsTimeseries(source)
  const { data: calData, isLoading: calLoading, isError: calError } = useCalibration(source)

  if (metricsLoading || calLoading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-8 w-48" />
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-52 w-full" />
        ))}
      </div>
    )
  }

  if (metricsError || calError) {
    return <ErrorMessage message="Failed to load model metrics" />
  }

  const models = metricsData?.models ?? []
  const calModels = calData?.models ?? []
  const fmt = (v: number) => (v * 100).toFixed(1) + '%'

  // Volume bar chart: daily sample counts from timeseries
  const volumeModel = tsData?.models.find((m) => m.model_name === 'pair_classifier')
  const volumeData = (volumeModel?.points ?? []).map((p) => ({
    bucket: new Intl.DateTimeFormat('en-GB', { month: 'short', day: 'numeric' }).format(new Date(p.bucket)),
    count: p.sample_count,
  }))

  return (
    <div className="flex flex-col gap-4">
      {/* Architecture summary */}
      <div className="bg-white rounded-lg border border-slate-200 p-5">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
          Cascade architecture
        </p>
        <div className="flex flex-col gap-3">
          {(['prompt_detector', 'pair_classifier', 'taxonomy_classifier'] as const).map((key) => (
            <div key={key} className="flex gap-3 items-start">
              <span
                className="shrink-0 mt-0.5 w-2.5 h-2.5 rounded-full"
                style={{ background: MODEL_COLORS[key] }}
              />
              <div>
                <span className="text-xs font-semibold text-slate-800">{MODEL_DISPLAY[key]}</span>
                <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{MODEL_ROLE[key]}</p>
              </div>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-400 mt-3 border-t border-slate-100 pt-3">
          All three are fine-tuned RoBERTa-base (~125M params). At inference the pair classifier
          runs in ~6 ms on CPU — 80× faster than Llama Guard 3 (8B) while matching or exceeding its F1.
        </p>
      </div>

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

      {/* Summary metrics table */}
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
                  <td className="px-4 py-2 font-mono text-xs text-slate-700">
                    {MODEL_DISPLAY[m.model_name] ?? m.model_name}
                  </td>
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

      {/* Volume bar chart — daily event counts */}
      {volumeData.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 p-5">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
            Daily evaluation volume
          </p>
          <div className="h-36 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={volumeData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="bucket" tick={{ fontSize: 9 }} />
                <YAxis tick={{ fontSize: 9 }} />
                <Tooltip formatter={(v: any) => [Number(v).toLocaleString(), 'events'] as any} />
                <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                  {volumeData.map((_, i) => (
                    <Cell key={i} fill={MODEL_COLORS.pair_classifier} fillOpacity={0.7} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Calibration reliability diagrams */}
      {calModels.length > 0 && (
        <>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mt-2">
            Calibration reliability diagrams
          </p>
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
