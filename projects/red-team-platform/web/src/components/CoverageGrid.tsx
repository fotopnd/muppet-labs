import { useState } from 'react'
import { abbrevName, labelName } from '@/lib/categoryLabels'

export type CoverageGridCell = {
  row_label: string
  col_label: string
  asr: number | null
  total_runs: number
  total_successes: number
}

type CoverageGridProps = {
  cells: CoverageGridCell[]
  rowLabels: string[]
  colLabels: string[]
  cellWidth?: number
  cellHeight?: number
  compact?: boolean
}

function asrColour(asr: number): string {
  const hue = Math.round(120 * (1 - asr))
  return `hsl(${hue}, 65%, 45%)`
}

type TooltipState = {
  cell: CoverageGridCell
  x: number
  y: number
} | null

export function CoverageGrid({
  cells,
  rowLabels,
  colLabels,
  cellWidth = 60,
  cellHeight = 48,
  compact = false,
}: CoverageGridProps) {
  const cw = compact ? 35 : cellWidth
  const ch = compact ? 28 : cellHeight
  const [tooltip, setTooltip] = useState<TooltipState>(null)

  const cellMap = new Map(cells.map((c) => [`${c.row_label}|${c.col_label}`, c]))
  const rowHeaderWidth = 100

  const headerFontSize = compact ? 9 : 11

  return (
    <div className="relative overflow-x-auto">
      {/* Column headers */}
      <div
        className="flex"
        style={{ marginLeft: rowHeaderWidth, marginBottom: 2 }}
      >
        {colLabels.map((col) => (
          <div
            key={col}
            style={{ width: cw, minWidth: cw, fontSize: headerFontSize }}
            className="text-center text-text-secondary font-medium px-0.5 truncate"
            title={labelName(col)}
          >
            {compact ? abbrevName(col) : labelName(col).slice(0, 12)}
          </div>
        ))}
      </div>

      {/* Rows */}
      {rowLabels.map((row) => (
        <div key={row} className="flex items-center" style={{ height: ch, marginBottom: 1 }}>
          <div
            className="text-xs text-text-secondary font-medium truncate pr-2 text-right"
            style={{ width: rowHeaderWidth, minWidth: rowHeaderWidth, fontSize: headerFontSize }}
            title={row}
          >
            {row}
          </div>
          {colLabels.map((col) => {
            const cell = cellMap.get(`${row}|${col}`)
            return (
              <div
                key={col}
                style={{
                  width: cw,
                  minWidth: cw,
                  height: ch,
                  backgroundColor: cell && cell.asr !== null ? asrColour(cell.asr) : undefined,
                }}
                className={`flex items-center justify-center cursor-default ${
                  !cell || cell.asr === null ? 'bg-surface-muted' : ''
                }`}
                onMouseEnter={(e) => {
                  if (cell) setTooltip({ cell, x: e.clientX, y: e.clientY })
                }}
                onMouseMove={(e) => {
                  if (cell) setTooltip({ cell, x: e.clientX, y: e.clientY })
                }}
                onMouseLeave={() => setTooltip(null)}
              >
                {cell && cell.asr !== null ? (
                  <span
                    className="font-mono font-semibold text-white select-none"
                    style={{ fontSize: compact ? 8 : 11 }}
                  >
                    {(cell.asr * 100).toFixed(0)}%
                  </span>
                ) : (
                  <span className="text-text-muted select-none" style={{ fontSize: compact ? 8 : 11 }}>—</span>
                )}
              </div>
            )
          })}
        </div>
      ))}

      {/* Tooltip */}
      {tooltip && (
        <div
          className="fixed z-50 bg-canvas border border-border rounded p-2 text-xs shadow-lg pointer-events-none"
          style={{ left: tooltip.x + 12, top: tooltip.y - 8 }}
        >
          <p className="font-semibold text-text-primary">{labelName(tooltip.cell.col_label)}</p>
          <p className="text-text-secondary">Strategy: {tooltip.cell.row_label}</p>
          <p className="text-text-secondary">
            ASR: {tooltip.cell.asr !== null ? `${(tooltip.cell.asr * 100).toFixed(1)}%` : '—'}
          </p>
          <p className="text-text-secondary">
            n={tooltip.cell.total_runs} | successes={tooltip.cell.total_successes}
          </p>
        </div>
      )}
    </div>
  )
}
