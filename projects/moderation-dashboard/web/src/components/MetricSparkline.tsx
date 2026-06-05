import { Line, LineChart, ReferenceLine, ResponsiveContainer } from 'recharts'

const ACCENT_HEX = '#2563eb'
const BASELINE_HEX = '#94a3b8'  // slate-400

type MetricSparklineProps = {
  data: number[]
  label: string
  currentValue: number | null
  baselineValue?: number | null
}

export function MetricSparkline({ data, label, currentValue, baselineValue }: MetricSparklineProps) {
  const chartData =
    data.length < 2
      ? [{ value: 0 }, { value: 0 }]
      : data.map(v => ({ value: v }))

  const displayValue = currentValue !== null ? currentValue.toFixed(3) : '—'

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-baseline justify-between">
        <span className="font-interface text-xs text-text-muted uppercase tracking-wide">
          {label}
        </span>
        <span className="font-data text-sm font-medium text-text-intense">
          {displayValue}
        </span>
      </div>
      <div className="h-12 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 2, right: 0, bottom: 2, left: 0 }}>
            {baselineValue != null && (
              <ReferenceLine
                y={baselineValue}
                stroke={BASELINE_HEX}
                strokeDasharray="3 3"
                strokeWidth={1}
              />
            )}
            <Line
              type="monotone"
              dataKey="value"
              stroke={ACCENT_HEX}
              dot={false}
              strokeWidth={1.5}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
