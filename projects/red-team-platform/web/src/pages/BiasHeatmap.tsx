import { Fragment } from 'react'
import { BiasCell } from '@/components/BiasCell'
import { useBiasScores } from '@/hooks/useBiasScores'
import type { BiasScoreRow } from '@/types'

function groupByGovernment(rows: BiasScoreRow[]): [string, BiasScoreRow[]][] {
  const map = new Map<string, BiasScoreRow[]>()
  for (const row of rows) {
    const group = map.get(row.government) ?? []
    group.push(row)
    map.set(row.government, group)
  }
  return Array.from(map.entries())
}

export function BiasHeatmap() {
  const { data, isLoading, isError } = useBiasScores()

  if (isLoading)
    return <p className="p-4 text-text-secondary">Loading bias scores…</p>
  if (isError)
    return <p className="p-4 text-danger">Error loading bias scores.</p>

  if (!data || data.rows.length === 0)
    return (
      <div className="p-4">
        <h2 className="mb-2 text-lg font-semibold text-text-primary">
          Language Bias Heatmap
        </h2>
        <p className="text-text-muted text-sm">
          No scores yet. Run{' '}
          <code className="font-mono bg-surface-muted px-1 rounded text-xs">
            seed-bias-corpus
          </code>{' '}
          then{' '}
          <code className="font-mono bg-surface-muted px-1 rounded text-xs">
            attack --mode bias --language &lt;lang&gt;
          </code>{' '}
          then{' '}
          <code className="font-mono bg-surface-muted px-1 rounded text-xs">
            score-bias
          </code>
          .
        </p>
      </div>
    )

  const groups = groupByGovernment(data.rows)

  return (
    <div className="p-4 overflow-x-auto">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text-primary">
          Language Bias Heatmap
        </h2>
        <span className="text-xs text-text-muted font-mono bg-surface-muted px-2 py-1 rounded">
          {data.scored_model ?? 'No scores yet'}
        </span>
      </div>

      <div className="mb-3 flex gap-4 text-xs text-text-muted">
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm bg-divergence-null" /> null
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm bg-divergence-low" /> 0.00–0.14
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm bg-divergence-mid" /> 0.15–0.34
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm bg-divergence-high" /> 0.35+
        </span>
      </div>

      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-surface-muted">
            <th className="text-left p-2 font-medium text-text-secondary border-b border-border">
              Topic
            </th>
            <th className="p-2 font-medium text-text-secondary border-b border-border w-20 text-center">
              ZH
            </th>
            <th className="p-2 font-medium text-text-secondary border-b border-border w-20 text-center">
              RU
            </th>
            <th className="p-2 font-medium text-text-secondary border-b border-border w-20 text-center">
              AR
            </th>
          </tr>
        </thead>
        <tbody>
          {groups.map(([government, rows]) => (
            <Fragment key={government}>
              <tr className="bg-accent-subtle">
                <td
                  colSpan={4}
                  className="p-2 font-semibold text-accent text-xs uppercase tracking-wider"
                >
                  {government}
                </td>
              </tr>
              {rows.map((row) => (
                <tr
                  key={row.topic_id}
                  className="border-b border-border hover:bg-surface-muted transition-colors"
                >
                  <td className="p-2 text-text-primary">{row.label}</td>
                  <BiasCell score={row.zh_score} />
                  <BiasCell score={row.ru_score} />
                  <BiasCell score={row.ar_score} />
                </tr>
              ))}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  )
}
