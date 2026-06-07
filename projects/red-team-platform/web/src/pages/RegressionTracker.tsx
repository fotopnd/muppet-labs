import { CartesianGrid, Legend, Line, LineChart, Tooltip, XAxis, YAxis } from 'recharts'
import { useRegression } from '@/hooks/useRegression'
import type { RegressionPoint } from '@/types'

const COLOURS = ['#4f46e5', '#e11d48', '#16a34a', '#ca8a04', '#0ea5e9'] as const

function getColour(i: number): string {
  return COLOURS[i % COLOURS.length] ?? '#4f46e5'
}

export function RegressionTracker() {
  const { data, isLoading, isError } = useRegression()

  if (isLoading) return <p style={{ padding: '1rem' }}>Loading...</p>
  if (isError) return <p style={{ padding: '1rem', color: 'red' }}>Error loading regression data.</p>
  if (!data || data.points.length === 0) return <p style={{ padding: '1rem' }}>No regression data yet.</p>

  const { points, model_names: modelNames } = data

  const seriesByModel: Record<string, RegressionPoint[]> = Object.fromEntries(
    modelNames.map((name) => [name, points.filter((p) => p.model_name === name)]),
  )

  const allDates = [...new Set(points.map((p) => p.created_at))].sort()
  const chartData = allDates.map((date) => {
    const row: Record<string, string | number> = { date: date.slice(0, 10) }
    for (const name of modelNames) {
      const pt = seriesByModel[name]?.find((p) => p.created_at === date)
      if (pt) row[name] = +(pt.asr * 100).toFixed(1)
    }
    return row
  })

  return (
    <div style={{ padding: '1rem', overflowX: 'auto' }}>
      <h2>Regression Tracker</h2>
      <LineChart width={800} height={400} data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis tickFormatter={(v: number) => `${v}%`} domain={[0, 100]} />
        <Tooltip />
        <Legend />
        {modelNames.map((name, i) => (
          <Line
            key={name}
            type="monotone"
            dataKey={name}
            stroke={getColour(i)}
            dot={true}
            connectNulls
          />
        ))}
      </LineChart>
    </div>
  )
}
