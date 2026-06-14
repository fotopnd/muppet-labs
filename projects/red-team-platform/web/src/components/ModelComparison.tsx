import { useMemo } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, Tooltip, XAxis, YAxis } from 'recharts'
import { useStrategyComparisonByModel, MODEL_KEYS } from '@/hooks/useStrategyComparisonByModel'

const WAVE_STRATEGIES = [
  'AIM', 'evil_confidant', 'few_shot_json', 'refusal_suppression', 'combination_1',
  'dev_mode_v2', 'prefix_injection', 'distractors', 'evil_system_prompt', 'multi_shot_25',
  'gcg', 'base64', 'rot13',
]

const MODEL_FILL: Record<string, string> = {
  'gemma2:9b':    '#3b82f6',
  'qwen2.5:7b':  '#f97316',
  'llama3.1:8b': '#8b5cf6',
}

const MODEL_SHORT: Record<string, string> = {
  'gemma2:9b':    'gemma2',
  'qwen2.5:7b':  'qwen2.5',
  'llama3.1:8b': 'llama3.1',
}

export function ModelComparison() {
  const { byStrategy, isLoading, isError } = useStrategyComparisonByModel()

  const chartData = useMemo(() => {
    return WAVE_STRATEGIES.map((strategy) => {
      const row: Record<string, string | number> = { strategy }
      for (const m of MODEL_KEYS) {
        const asr = byStrategy[strategy]?.[m]
        row[MODEL_SHORT[m]!] = asr !== undefined ? +(asr * 100).toFixed(1) : 0
      }
      return row
    })
  }, [byStrategy])

  if (isLoading) return <p className="text-text-secondary text-sm">Loading…</p>
  if (isError) return <p className="text-danger text-sm">Error loading model comparison.</p>

  return (
    <div>
      {/* Prose callout */}
      <div className="bg-surface-muted rounded-lg p-4 mb-4 text-sm">
        <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
          Model Safety Summary
        </p>
        <ul className="space-y-1.5 text-text-primary">
          <li>
            <span className="text-blue-700 font-semibold">gemma2:9b</span>
            <span className="text-text-secondary ml-1">
              (Google) — most vulnerable, ~31.8% avg ASR. AIM persona injection exceeded 55%.
            </span>
          </li>
          <li>
            <span className="text-orange-700 font-semibold">qwen2.5:7b</span>
            <span className="text-text-secondary ml-1">
              (Alibaba) — ~26.2% avg ASR. Resistant to persona attacks; vulnerable to prompt injection strategies.
            </span>
          </li>
          <li>
            <span className="text-violet-700 font-semibold">llama3.1:8b</span>
            <span className="text-text-secondary ml-1">
              (Meta) — most resistant, ~4.0% avg ASR. Only refusal suppression and ROT-13 exceeded 10%.
            </span>
          </li>
        </ul>
      </div>

      {/* Grouped bar chart */}
      <div className="bg-surface border border-border rounded-lg p-4 overflow-x-auto">
        <p className="text-xs text-text-muted mb-3">
          ASR per strategy × model. Lower is safer.
        </p>
        <BarChart
          width={680}
          height={340}
          data={chartData}
          margin={{ top: 8, right: 16, bottom: 60, left: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
          <XAxis
            dataKey="strategy"
            tick={{ fontSize: 9 }}
            angle={-35}
            textAnchor="end"
            height={70}
          />
          <YAxis
            tickFormatter={(v: number) => `${v}%`}
            domain={[0, 100]}
            tick={{ fontSize: 10 }}
          />
          <Tooltip formatter={(v: number) => `${v}%`} />
          <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
          {MODEL_KEYS.map((m) => (
            <Bar key={m} dataKey={MODEL_SHORT[m]!} fill={MODEL_FILL[m]} />
          ))}
        </BarChart>
      </div>
    </div>
  )
}
