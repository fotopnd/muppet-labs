import { useMemo } from 'react'
import { Bar, BarChart, CartesianGrid, LabelList, Tooltip, XAxis, YAxis } from 'recharts'
import { useStrategyComparison } from '@/hooks/useStrategyComparison'
import { useCoverage } from '@/hooks/useCoverage'
import { CoverageGrid } from '@/components/CoverageGrid'
import type { CoverageGridCell } from '@/components/CoverageGrid'

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

  if (isLoading) return <p className="p-4 text-text-secondary text-sm">Loading…</p>
  if (isError) return <p className="p-4 text-danger text-sm">Error loading strategy data.</p>
  if (!data || data.bars.length === 0) return <p className="p-4 text-text-muted text-sm">No strategy data yet.</p>

  const sortedByAsr = [...data.bars].sort((a, b) => b.asr - a.asr)
  const sortedByVol = [...data.bars].sort((a, b) => b.total_runs - a.total_runs)

  const asrData = sortedByAsr.map((b) => ({
    strategy: b.strategy,
    asr_pct: +(b.asr * 100).toFixed(1),
    n: b.total_runs,
  }))
  const volData = sortedByVol.map((b) => ({
    strategy: b.strategy,
    total_runs: b.total_runs,
  }))

  return (
    <div className="p-4">
      <h2 className="text-base font-semibold text-text-primary mb-4">Strategy Comparison</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Panel A: ASR by strategy */}
        <div className="bg-surface border border-border rounded-lg p-4">
          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
            ASR % by Strategy
          </p>
          <BarChart width={260} height={280} data={asrData} margin={{ top: 16, right: 8, bottom: 60, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis dataKey="strategy" angle={-30} textAnchor="end" tick={{ fontSize: 10 }} />
            <YAxis tickFormatter={(v: number) => `${v}%`} domain={[0, 100]} tick={{ fontSize: 10 }} />
            <Tooltip
              content={({ payload }) => {
                if (!payload?.length) return null
                const d = payload[0]?.payload as typeof asrData[number]
                return (
                  <div className="bg-canvas border border-border rounded p-2 text-xs shadow">
                    <p className="font-semibold text-text-primary">{d.strategy}</p>
                    <p className="text-text-secondary">ASR: {d.asr_pct}%</p>
                    <p className="text-text-secondary">n={d.n}</p>
                  </div>
                )
              }}
            />
            <Bar dataKey="asr_pct" fill="var(--color-danger)" name="ASR %">
              <LabelList dataKey="n" position="top" formatter={(v: number) => `n=${v}`} style={{ fontSize: 9 }} />
            </Bar>
          </BarChart>
        </div>

        {/* Panel B: Volume by strategy */}
        <div className="bg-surface border border-border rounded-lg p-4">
          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
            Attack Volume by Strategy
          </p>
          <BarChart
            width={260}
            height={280}
            data={volData}
            layout="vertical"
            margin={{ top: 4, right: 24, bottom: 4, left: 80 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 10 }} />
            <YAxis type="category" dataKey="strategy" tick={{ fontSize: 10 }} width={74} />
            <Tooltip
              content={({ payload }) => {
                if (!payload?.length) return null
                const d = payload[0]?.payload as typeof volData[number]
                return (
                  <div className="bg-canvas border border-border rounded p-2 text-xs shadow">
                    <p className="font-semibold text-text-primary">{d.strategy}</p>
                    <p className="text-text-secondary">Runs: {d.total_runs}</p>
                  </div>
                )
              }}
            />
            <Bar dataKey="total_runs" fill="var(--color-accent)" name="Runs" />
          </BarChart>
        </div>

        {/* Panel C: Compact coverage grid */}
        <div className="bg-surface border border-border rounded-lg p-4 overflow-x-auto">
          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
            Strategy × Category Coverage
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
      </div>
    </div>
  )
}
