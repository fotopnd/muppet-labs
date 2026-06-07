import { Cell, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts'
import { useCoverage } from '@/hooks/useCoverage'

function asrToColour(asr: number): string {
  const hue = Math.round(120 * (1 - asr))
  return `hsl(${hue}, 70%, 45%)`
}

export function CoverageHeatmap() {
  const { data, isLoading, isError } = useCoverage()

  if (isLoading) return <p style={{ padding: '1rem' }}>Loading...</p>
  if (isError) return <p style={{ padding: '1rem', color: 'red' }}>Error loading coverage.</p>
  if (!data || data.cells.length === 0) return <p style={{ padding: '1rem' }}>No coverage data yet.</p>

  const { harm_categories: harmCategories, strategies, cells } = data

  const chartData = cells.map((cell) => ({
    x: harmCategories.indexOf(cell.harm_category),
    y: strategies.indexOf(cell.strategy),
    asr: cell.asr,
    harm_category: cell.harm_category,
    strategy: cell.strategy,
    total_runs: cell.total_runs,
    total_successes: cell.total_successes,
  }))

  return (
    <div style={{ padding: '1rem', overflowX: 'auto' }}>
      <h2>Coverage Heatmap</h2>
      <ScatterChart width={900} height={400} margin={{ top: 20, right: 20, bottom: 60, left: 60 }}>
        <XAxis
          type="number"
          dataKey="x"
          ticks={harmCategories.map((_, i) => i)}
          tickFormatter={(i: number) => harmCategories[i] ?? ''}
          angle={-30}
          textAnchor="end"
          tick={{ fontSize: 11 }}
        />
        <YAxis
          type="number"
          dataKey="y"
          ticks={strategies.map((_, i) => i)}
          tickFormatter={(i: number) => strategies[i] ?? ''}
          tick={{ fontSize: 11 }}
        />
        <Tooltip
          content={({ payload }) => {
            if (!payload || payload.length === 0) return null
            const d = payload[0]?.payload as typeof chartData[number] | undefined
            if (!d) return null
            return (
              <div style={{ background: '#fff', border: '1px solid #ccc', padding: '0.5rem', fontSize: '0.8rem' }}>
                <div><b>{d.harm_category}</b></div>
                <div>Strategy: {d.strategy}</div>
                <div>ASR: {(d.asr * 100).toFixed(1)}%</div>
                <div>Runs: {d.total_runs} | Successes: {d.total_successes}</div>
              </div>
            )
          }}
        />
        <Scatter data={chartData} shape="square">
          {chartData.map((entry, idx) => (
            <Cell key={idx} fill={asrToColour(entry.asr)} />
          ))}
        </Scatter>
      </ScatterChart>
    </div>
  )
}
