import { useMemo } from 'react'
import {
  Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { useStrategyComparison } from '@/hooks/useStrategyComparison'
import { useCoverage } from '@/hooks/useCoverage'
import { CoverageGrid } from '@/components/CoverageGrid'
import { AnalyticsSummary } from '@/components/AnalyticsSummary'
import type { CoverageGridCell } from '@/components/CoverageGrid'

function asrColour(asr_pct: number): string {
  if (asr_pct < 30) return 'var(--color-success)'
  if (asr_pct < 60) return 'var(--color-warning)'
  return 'var(--color-danger)'
}

export function StrategyComparison() {
  const { data, isLoading, isError } = useStrategyComparison()
  const { data: coverageData } = useCoverage()

  const compactCells = useMemo((): CoverageGridCell[] => {
    if (!coverageData) return []
    return coverageData.cells.map((c) => ({
      row_label: c.strategy,
      col_label: c.harm_category,
      asr: c.asr,
      total_runs: c.total_runs,
      total_successes: c.total_successes,
    }))
  }, [coverageData])

  if (isLoading) return <p className="text-text-secondary text-sm">Loading…</p>
  if (isError) return <p className="text-danger text-sm">Error loading strategy data.</p>
  if (!data || data.bars.length === 0) return <p className="text-text-muted text-sm">No strategy data yet.</p>

  const chartData = [...data.bars]
    .filter((b) => !['none', 'original_prompt'].includes(b.strategy))
    .sort((a, b) => b.asr - a.asr)
    .map((b) => ({
      strategy: b.strategy,
      asr_pct: +(b.asr * 100).toFixed(1),
    }))

  return (
    <div className="space-y-6">
      {/* ASR by strategy — horizontal bar chart */}
      <div className="bg-surface border border-border rounded-lg p-4">
        <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1">
          Attack Success Rate by Strategy (aggregate, 3 models)
        </p>
        <p className="text-xs text-text-muted mb-3">
          Sorted high → low. Each strategy: ~300 attacks × 3 models ≈ 900 runs. Colour: green &lt;30%, amber 30–60%, red ≥60%.
        </p>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 4, right: 48, bottom: 4, left: 120 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
            <XAxis
              type="number"
              tickFormatter={(v: number) => `${v}%`}
              domain={[0, 100]}
              tick={{ fontSize: 10 }}
            />
            <YAxis
              type="category"
              dataKey="strategy"
              tick={{ fontSize: 11, fontFamily: 'ui-monospace, monospace' }}
              width={114}
            />
            <Tooltip
              formatter={(v) => [`${v}%`, 'ASR']}
              contentStyle={{ fontSize: 12 }}
            />
            <Bar dataKey="asr_pct" name="ASR %">
              {chartData.map((entry, i) => (
                <Cell key={i} fill={asrColour(entry.asr_pct)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Strategy × Category coverage grid — full width */}
      <div className="bg-surface border border-border rounded-lg p-4 overflow-x-auto">
        <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1">
          Strategy × Harm Category Coverage
        </p>
        <p className="text-xs text-text-muted mb-3">
          ASR per cell across all models. Hover for detail.
        </p>
        {coverageData && coverageData.cells.length > 0 ? (
          <CoverageGrid
            cells={compactCells}
            rowLabels={coverageData.strategies}
            colLabels={coverageData.harm_categories}
            compact
          />
        ) : (
          <p className="text-text-muted text-xs">No coverage data.</p>
        )}
      </div>

      <AnalyticsSummary />
    </div>
  )
}
