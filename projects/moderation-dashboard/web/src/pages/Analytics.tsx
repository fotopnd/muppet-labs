import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { ErrorMessage } from '@/components/ErrorMessage'
import { useAnalytics } from '@/api/analytics'

// Fixed palette — one colour per model. Update if MODEL_REGISTRY changes.
const MODEL_COLOURS: Record<string, string> = {
  distilbert: '#2563eb',       // blue-600
  roberta: '#059669',          // emerald-600
  detoxify: '#f59e0b',         // amber-500
  finetuned_distilbert: '#7c3aed', // violet-600
  finetuned_roberta: '#e11d48',    // rose-600
}

function formatHour(isoString: string): string {
  const d = new Date(isoString)
  return `${d.getHours().toString().padStart(2, '0')}:00`
}

export function Analytics() {
  const { data, isLoading, isError } = useAnalytics()

  if (isError) {
    return <ErrorMessage title="Failed to load analytics" body="Retrying automatically…" />
  }

  if (isLoading) {
    return <p className="font-interface text-sm text-text-muted">Loading analytics…</p>
  }

  const noData =
    !data ||
    (data.category_trends.length === 0 &&
      data.model_accuracy.length === 0 &&
      data.escalation_rates.length === 0)

  if (noData) {
    return (
      <div className="bg-surface rounded-lg border border-border p-8 text-center">
        <p className="font-interface text-sm font-medium text-text-default">No analytics data yet</p>
        <p className="font-interface text-xs text-text-muted mt-1">
          Data will populate as events are processed by the stream.
        </p>
      </div>
    )
  }

  // Reshape model_accuracy for recharts: array of { hour, distilbert, roberta, ... }
  const accuracyByHour: Record<string, Record<string, number>> = {}
  for (const pt of data!.model_accuracy) {
    const hour = pt.hour
    if (!accuracyByHour[hour]) accuracyByHour[hour] = {}
    accuracyByHour[hour][pt.model_name] = pt.f1
  }
  const accuracyData = Object.entries(accuracyByHour)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([hour, vals]) => ({ hour: formatHour(hour), ...vals }))

  // Reshape category_trends: array of { hour, toxic, severe_toxic, ... }
  const categoryByHour: Record<string, Record<string, number>> = {}
  const allCategories = new Set<string>()
  for (const pt of data!.category_trends) {
    if (!categoryByHour[pt.hour]) categoryByHour[pt.hour] = {}
    categoryByHour[pt.hour][pt.category] = pt.event_count
    allCategories.add(pt.category)
  }
  const categoryData = Object.entries(categoryByHour)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([hour, vals]) => ({ hour: formatHour(hour), ...vals }))

  return (
    <div className="space-y-6">
      {/* Model accuracy over time */}
      <div className="bg-surface rounded-lg border border-border p-5">
        <h2 className="font-interface text-sm font-semibold text-text-intense mb-4">
          Model F1 over time (shadow group)
        </h2>
        {accuracyData.length === 0 ? (
          <p className="font-interface text-sm text-text-muted">No data</p>
        ) : (
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={accuracyData}>
                <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                {Object.entries(MODEL_COLOURS).map(([model, colour]) => (
                  <Line
                    key={model}
                    type="monotone"
                    dataKey={model}
                    stroke={colour}
                    dot={false}
                    strokeWidth={1.5}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Category trends */}
      <div className="bg-surface rounded-lg border border-border p-5">
        <h2 className="font-interface text-sm font-semibold text-text-intense mb-4">
          Category event volume (hourly)
        </h2>
        {categoryData.length === 0 ? (
          <p className="font-interface text-sm text-text-muted">No data</p>
        ) : (
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={categoryData}>
                <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                {Array.from(allCategories).map((cat, i) => (
                  <Line
                    key={cat}
                    type="monotone"
                    dataKey={cat}
                    stroke={Object.values(MODEL_COLOURS)[i % 5]}
                    dot={false}
                    strokeWidth={1.5}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Escalation rates */}
      <div className="bg-surface rounded-lg border border-border p-5">
        <h2 className="font-interface text-sm font-semibold text-text-intense mb-4">
          Escalation rate (5-min windows)
        </h2>
        {data!.escalation_rates.length === 0 ? (
          <p className="font-interface text-sm text-text-muted">No data</p>
        ) : (
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={data!.escalation_rates.slice().reverse().map(pt => ({
                  window: formatHour(pt.window_start),
                  rate: pt.escalation_rate,
                }))}
              >
                <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                <XAxis dataKey="window" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="rate"
                  stroke="#dc2626"
                  dot={false}
                  strokeWidth={1.5}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  )
}
