import {
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ModelTimeseries } from '@/types'

// stroke values are hardcoded — recharts cannot read CSS variables
const MODEL_COLORS: Record<string, string> = {
  pair_classifier: '#2563eb',
  prompt_detector: '#059669',
  taxonomy_classifier: '#f59e0b',
}

const FALLBACK_COLORS = ['#2563eb', '#059669', '#f59e0b', '#dc2626', '#7c3aed']

function formatBucket(iso: string): string {
  return new Intl.DateTimeFormat('en-GB', { month: 'short', day: 'numeric' }).format(
    new Date(iso),
  )
}

type Metric = 'f1' | 'precision' | 'recall'

type MergedPoint = { bucket: string; [key: string]: string | number }

function mergeTimeseries(models: ModelTimeseries[], metric: Metric): MergedPoint[] {
  const map = new Map<string, MergedPoint>()
  for (const model of models) {
    for (const pt of model.points) {
      if (!map.has(pt.bucket)) map.set(pt.bucket, { bucket: pt.bucket })
      map.get(pt.bucket)![model.model_name] = pt[metric]
    }
  }
  return [...map.values()].sort(
    (a, b) => new Date(a.bucket).getTime() - new Date(b.bucket).getTime(),
  )
}

type Props = {
  title: string
  metric: Metric
  models: ModelTimeseries[]
}

export function MetricComparisonChart({ title, metric, models }: Props) {
  const data = mergeTimeseries(models, metric)
  const modelNames = models.map((m) => m.model_name)

  if (data.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-5">
        <h3 className="font-sans text-sm font-semibold text-slate-900 mb-3">{title}</h3>
        <div className="h-40 flex items-center justify-center">
          <span className="font-sans text-xs text-slate-400">No timeseries data</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5">
      <h3 className="font-sans text-sm font-semibold text-slate-900 mb-3">{title}</h3>
      <div className="h-40 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
            <XAxis
              dataKey="bucket"
              tickFormatter={formatBucket}
              tick={{ fontSize: 10 }}
              interval="preserveStartEnd"
            />
            <YAxis domain={[0, 1]} tick={{ fontSize: 10 }} tickCount={3} />
            <Tooltip
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={(v: any) => (v as number).toFixed(3) as any}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              labelFormatter={(iso: any) => formatBucket(String(iso)) as any}
            />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            {modelNames.map((name, i) => (
              <Line
                key={name}
                type="monotone"
                dataKey={name}
                stroke={MODEL_COLORS[name] ?? FALLBACK_COLORS[i % FALLBACK_COLORS.length]}
                dot={false}
                strokeWidth={1.5}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
