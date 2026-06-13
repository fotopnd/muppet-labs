import { useMemo } from 'react'
import { useCoverage } from '@/hooks/useCoverage'
import { CoverageGrid } from '@/components/CoverageGrid'
import type { CoverageGridCell } from '@/components/CoverageGrid'
import { labelName } from '@/lib/categoryLabels'

export function CoverageHeatmap() {
  const { data, isLoading, isError } = useCoverage()

  const { cells, rowLabels, colLabels } = useMemo(() => {
    if (!data) return { cells: [], rowLabels: [], colLabels: [] }

    const meanAsr: Record<string, number> = {}
    for (const cat of data.harm_categories) {
      const catCells = data.cells.filter((c) => c.harm_category === cat)
      meanAsr[cat] = catCells.length ? catCells.reduce((s, c) => s + c.asr, 0) / catCells.length : 0
    }
    const sortedCols = [...data.harm_categories].sort((a, b) => (meanAsr[b] ?? 0) - (meanAsr[a] ?? 0))

    const gridCells: CoverageGridCell[] = data.cells.map((c) => ({
      row_label: c.strategy,
      col_label: c.harm_category,
      asr: c.asr,
      total_runs: c.total_runs,
      total_successes: c.total_successes,
    }))

    return { cells: gridCells, rowLabels: data.strategies, colLabels: sortedCols }
  }, [data])

  if (isLoading) return <p className="p-4 text-text-secondary text-sm">Loading…</p>
  if (isError) return <p className="p-4 text-danger text-sm">Error loading coverage.</p>
  if (!data || data.cells.length === 0) return <p className="p-4 text-text-muted text-sm">No coverage data yet.</p>

  return (
    <div className="p-4 overflow-x-auto">
      <h2 className="text-base font-semibold text-text-primary mb-1">Coverage Heatmap</h2>
      <p className="text-xs text-text-muted mb-4">
        Rows = strategies · Columns = harm categories sorted by mean ASR (high → low)
      </p>
      <div className="mb-3 flex gap-4 text-xs text-text-muted">
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm bg-green-600" /> Low ASR (safe)
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm bg-yellow-600" /> Medium
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm bg-red-600" /> High ASR (danger)
        </span>
      </div>
      <CoverageGrid
        cells={cells}
        rowLabels={rowLabels}
        colLabels={colLabels}
        cellWidth={62}
        cellHeight={48}
      />
      <p className="text-xs text-text-muted mt-3">
        Column labels show first 12 chars — hover a cell for full category name.
        Full names: {colLabels.map(labelName).join(' · ')}
      </p>
    </div>
  )
}
