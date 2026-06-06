import { CartesianGrid, Line, LineChart, ReferenceLine, Tooltip, XAxis, YAxis } from 'recharts'
import type { ModelCalibration } from '@/types'

type Props = { data: ModelCalibration }

export function CalibrationChart({ data }: Props) {
  const chartData = data.bins.map((b) => ({
    x: +((b.bin_lower + b.bin_upper) / 2).toFixed(2),
    actual: +b.actual_positive_rate.toFixed(3),
    count: b.count,
  }))

  return (
    <div>
      <h3 className="text-sm font-medium text-gray-700 mb-2">{data.model_name}</h3>
      <LineChart width={320} height={220} data={chartData} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="x" domain={[0, 1]} tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`} label={{ value: 'Confidence', position: 'insideBottom', offset: -4 }} />
        <YAxis domain={[0, 1]} tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`} label={{ value: 'Actual +', angle: -90, position: 'insideLeft' }} />
        <Tooltip formatter={(v: number) => `${(v * 100).toFixed(1)}%`} />
        <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="#94a3b8" strokeDasharray="4 4" label="Perfect" />
        <Line type="monotone" dataKey="actual" stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} name="Actual +" />
      </LineChart>
    </div>
  )
}
