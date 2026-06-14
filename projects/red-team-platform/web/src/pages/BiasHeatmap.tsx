import { Fragment, useEffect, useMemo, useState } from 'react'
import { BiasCell } from '@/components/BiasCell'
import { BiasResponseViewer } from '@/components/BiasResponseViewer'
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
  const [govFilter, setGovFilter] = useState('')
  const [topicFilter, setTopicFilter] = useState('')
  const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null)

  const governments = useMemo(
    () => ['', ...Array.from(new Set((data?.rows ?? []).map((r) => r.government))).sort()],
    [data],
  )

  const filtered = useMemo(
    () =>
      (data?.rows ?? [])
        .filter((r) => !govFilter || r.government === govFilter)
        .filter((r) => !topicFilter || r.label.toLowerCase().includes(topicFilter.toLowerCase())),
    [data, govFilter, topicFilter],
  )

  const groups = groupByGovernment(filtered)

  // Close viewer when filters change if selected topic disappears
  useEffect(() => {
    if (selectedTopicId && !filtered.some((r) => r.topic_id === selectedTopicId)) {
      setSelectedTopicId(null)
    }
  }, [filtered, selectedTopicId])

  // Keyboard close
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') setSelectedTopicId(null) }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  if (isLoading) return <p className="p-4 text-text-secondary text-sm">Loading bias scores…</p>
  if (isError) return <p className="p-4 text-danger text-sm">Error loading bias scores.</p>

  if (!data || data.rows.length === 0)
    return (
      <div className="p-4">
        <h2 className="mb-2 text-base font-semibold text-text-primary">Language Bias Heatmap</h2>
        <p className="text-text-muted text-sm">
          No scores yet. Run{' '}
          <code className="font-mono bg-surface-muted px-1 rounded text-xs">seed-bias-corpus</code>{' '}
          then{' '}
          <code className="font-mono bg-surface-muted px-1 rounded text-xs">attack --mode bias --language &lt;lang&gt;</code>{' '}
          then{' '}
          <code className="font-mono bg-surface-muted px-1 rounded text-xs">score-bias</code>.
        </p>
      </div>
    )

  return (
    <div className="p-4 overflow-x-auto">
      <div className="mb-4 flex items-center justify-between flex-wrap gap-2">
        <h2 className="text-base font-semibold text-text-primary">Language Bias Heatmap</h2>
        <span className="text-xs text-text-muted font-mono bg-surface-muted px-2 py-1 rounded">
          {data.scored_model ?? 'No scores yet'}
        </span>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-4 flex-wrap">
        <select
          value={govFilter}
          onChange={(e) => setGovFilter(e.target.value)}
          className="px-2 py-1 text-sm border border-border rounded bg-surface text-text-primary"
        >
          {governments.map((g) => (
            <option key={g} value={g}>{g || 'All countries'}</option>
          ))}
        </select>
        <input
          placeholder="Filter by topic…"
          value={topicFilter}
          onChange={(e) => setTopicFilter(e.target.value)}
          className="px-2 py-1 text-sm border border-border rounded bg-surface text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-accent"
        />
      </div>

      {/* Legend */}
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
            <th className="text-left p-2 font-medium text-text-secondary border-b border-border">Topic</th>
            <th className="p-2 font-medium text-text-secondary border-b border-border w-20 text-center">EN</th>
            <th className="p-2 font-medium text-text-secondary border-b border-border w-20 text-center">ZH</th>
            <th className="p-2 font-medium text-text-secondary border-b border-border w-20 text-center">RU</th>
            <th className="p-2 font-medium text-text-secondary border-b border-border w-20 text-center">AR</th>
          </tr>
        </thead>
        <tbody>
          {groups.map(([government, rows]) => (
            <Fragment key={government}>
              <tr className="bg-accent-subtle">
                <td colSpan={5} className="p-2 font-semibold text-accent text-xs uppercase tracking-wider">
                  {government}
                </td>
              </tr>
              {rows.map((row) => (
                <Fragment key={row.topic_id}>
                  <tr
                    onClick={() => setSelectedTopicId(selectedTopicId === row.topic_id ? null : row.topic_id)}
                    className={`border-b border-border cursor-pointer transition-colors ${
                      selectedTopicId === row.topic_id ? 'bg-accent-subtle' : 'hover:bg-surface-muted'
                    }`}
                  >
                    <td className="p-2 text-text-primary">{row.label}</td>
                    {/* EN baseline column — always 0.00 */}
                    <td className="p-2 text-center w-20">
                      <span className="inline-flex items-center justify-center w-14 h-7 rounded text-xs font-mono font-semibold bg-divergence-low text-text-inverse">
                        0.00
                      </span>
                    </td>
                    <BiasCell score={row.zh_score} />
                    <BiasCell score={row.ru_score} />
                    <BiasCell score={row.ar_score} />
                  </tr>
                  {selectedTopicId === row.topic_id && (
                    <tr>
                      <td colSpan={5} className="p-0">
                        <div className="border-b border-border bg-surface p-4">
                          <BiasResponseViewer topicId={row.topic_id} model={data.scored_model ?? undefined} />
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </Fragment>
          ))}
        </tbody>
      </table>

      <div className="mt-3 space-y-1">
        <p className="text-xs text-text-muted">
          EN = 0.00 baseline — all values measure cosine distance from the English response.
          Higher scores indicate greater semantic divergence from the English answer.
        </p>
        <p className="text-xs text-text-muted">
          Scored using <span className="font-mono">{data.scored_model ?? 'gemma2:9b'}</span> only.
          Other models not yet evaluated for language bias.
        </p>
        <p className="text-xs text-text-muted">
          1.00 indicates maximum divergence — the model likely refused in that language while complying in English, or produced a qualitatively different response.
        </p>
      </div>
    </div>
  )
}
