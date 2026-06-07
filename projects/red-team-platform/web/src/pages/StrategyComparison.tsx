import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from 'recharts'
import { useStrategyComparison } from '@/hooks/useStrategyComparison'

export function StrategyComparison() {
  const { data, isLoading, isError } = useStrategyComparison()

  if (isLoading) return <p style={{ padding: '1rem' }}>Loading...</p>
  if (isError) return <p style={{ padding: '1rem', color: 'red' }}>Error loading strategy data.</p>
  if (!data || data.bars.length === 0) return <p style={{ padding: '1rem' }}>No strategy data yet.</p>

  const sorted = [...data.bars].sort((a, b) => b.asr - a.asr)
  const chartData = sorted.map((b) => ({ ...b, asr_pct: +(b.asr * 100).toFixed(1) }))

  return (
    <div style={{ padding: '1rem', overflowX: 'auto' }}>
      <h2>Strategy Comparison</h2>
      <BarChart width={800} height={400} data={chartData} margin={{ top: 20, right: 20, bottom: 60, left: 20 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="strategy" angle={-30} textAnchor="end" tick={{ fontSize: 11 }} />
        <YAxis tickFormatter={(v: number) => `${v}%`} domain={[0, 100]} />
        <Tooltip
          content={({ payload, label }) => {
            if (!payload || payload.length === 0) return null
            const d = payload[0]?.payload as (typeof chartData)[number] | undefined
            if (!d) return null
            return (
              <div
                style={{ background: '#fff', border: '1px solid #ccc', padding: '0.5rem', fontSize: '0.8rem' }}
              >
                <div>
                  <b>{label as string}</b>
                </div>
                <div>ASR: {d.asr_pct}%</div>
                <div>
                  Runs: {d.total_runs} | Successes: {d.total_successes}
                </div>
              </div>
            )
          }}
        />
        <Bar dataKey="asr_pct" fill="#4f46e5" name="ASR" />
      </BarChart>
    </div>
  )
}
