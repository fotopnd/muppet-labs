import { Line, LineChart, ResponsiveContainer } from 'recharts'

// recharts stroke cannot read CSS variables — hardcode accent token value.
// If accent hue changes, update this hex value to match tailwind.config.js.
const ACCENT_HEX = '#2563eb'

type MetricSparklineProps = {
  data: number[]
}

export function MetricSparkline({ data }: MetricSparklineProps) {
  const chartData =
    data.length < 2
      ? [{ value: 0 }, { value: 0 }]
      : data.map(v => ({ value: v }))

  return (
    <div className="h-12 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 2, right: 0, bottom: 2, left: 0 }}>
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
  )
}
