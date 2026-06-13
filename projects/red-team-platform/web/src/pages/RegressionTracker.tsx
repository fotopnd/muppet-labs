import { useMemo, useState } from 'react'
import {
  Bar, BarChart, CartesianGrid, Cell, LabelList, Legend,
  Line, LineChart, ReferenceLine, Tooltip, XAxis, YAxis,
} from 'recharts'
import { useRegression } from '@/hooks/useRegression'
import { useSessions } from '@/hooks/useSessions'
import { useCategoryDelta } from '@/hooks/useCategoryDelta'
import { StatWidget } from '@/components/StatWidget'
import { RegressionSummary } from '@/components/RegressionSummary'
import { labelName } from '@/lib/categoryLabels'
import type { RegressionPoint, Session } from '@/types'

const COLOURS = ['#4f46e5', '#e11d48', '#16a34a', '#ca8a04', '#0ea5e9'] as const
function getColour(i: number): string { return COLOURS[i % COLOURS.length] ?? '#4f46e5' }

export function RegressionTracker() {
  const { data, isLoading, isError } = useRegression()
  const { data: sessions } = useSessions()
  const [selectedModel, setSelectedModel] = useState<string | null>(null)
  const { data: deltaData } = useCategoryDelta(selectedModel)

  const resolvedModel = selectedModel ?? data?.model_names[0] ?? null

  const chartData = useMemo(() => {
    if (!data) return []
    const allDates = [...new Set(data.points.map((p) => p.created_at))].sort()
    const seriesByModel: Record<string, RegressionPoint[]> = Object.fromEntries(
      data.model_names.map((name) => [name, data.points.filter((p) => p.model_name === name)])
    )
    return allDates.map((date) => {
      const row: Record<string, string | number> = { date: date.slice(0, 10) }
      for (const name of (data.model_names ?? [])) {
        const pt = seriesByModel[name]?.find((p) => p.created_at === date)
        if (pt) row[name] = +(pt.asr * 100).toFixed(1)
      }
      return row
    })
  }, [data])

  const baselineAsr = useMemo(() => {
    if (!data || !resolvedModel) return null
    const first = data.points
      .filter((p) => p.model_name === resolvedModel)
      .sort((a, b) => a.created_at.localeCompare(b.created_at))[0]
    return first ? +(first.asr * 100).toFixed(1) : null
  }, [data, resolvedModel])

  const sessionRows = useMemo((): (Session & { delta: number | null })[] => {
    if (!sessions) return []
    const sorted = [...sessions].sort((a, b) => b.created_at.localeCompare(a.created_at))
    return sorted.map((s, i) => {
      const prev = sorted[i + 1]
      return { ...s, delta: prev ? s.asr - prev.asr : null }
    })
  }, [sessions])

  const bestCat = useMemo(() => {
    if (!deltaData?.items.length) return null
    return deltaData.items.reduce((best, x) => x.delta < best.delta ? x : best)
  }, [deltaData])

  const worstCat = useMemo(() => {
    if (!deltaData?.items.length) return null
    return deltaData.items.reduce((worst, x) => x.delta > worst.delta ? x : worst)
  }, [deltaData])

  const deltaChartData = useMemo(() => {
    if (!deltaData?.items.length) return []
    return [...deltaData.items].sort((a, b) => b.delta - a.delta).map((x) => ({
      category: labelName(x.harm_category).slice(0, 18),
      delta: +(x.delta * 100).toFixed(1),
    }))
  }, [deltaData])

  if (isLoading) return <p className="text-text-secondary text-sm">Loading…</p>
  if (isError) return <p className="text-danger text-sm">Error loading regression data.</p>
  if (!data || data.points.length === 0) return <p className="text-text-muted text-sm">No regression data yet.</p>

  return (
    <div>
      <div className="flex justify-end mb-4">
        {data.model_names.length > 1 && (
          <select
            value={selectedModel ?? ''}
            onChange={(e) => setSelectedModel(e.target.value || null)}
            className="px-2 py-1 text-sm border border-border rounded bg-surface text-text-primary"
          >
            <option value="">All models</option>
            {data.model_names.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Panel A: Overall ASR line chart */}
        <div className="bg-surface border border-border rounded-lg p-4">
          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
            Overall ASR Over Sessions
          </p>
          <LineChart width={380} height={260} data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis dataKey="date" tick={{ fontSize: 10 }} />
            <YAxis tickFormatter={(v: number) => `${v}%`} domain={[0, 100]} tick={{ fontSize: 10 }} />
            <Tooltip />
            <Legend />
            {baselineAsr !== null && (
              <ReferenceLine
                y={baselineAsr}
                stroke="var(--color-text-muted)"
                strokeDasharray="4 2"
                label={{ value: 'Baseline', fontSize: 10 }}
              />
            )}
            {(data.model_names ?? []).map((name, i) => (
              <Line key={name} type="monotone" dataKey={name} stroke={getColour(i)} dot connectNulls>
                <LabelList dataKey={name} position="top" formatter={(v: number) => `${v}%`} style={{ fontSize: 9 }} />
              </Line>
            ))}
          </LineChart>
        </div>

        {/* Panel B: Category delta */}
        <div className="bg-surface border border-border rounded-lg p-4">
          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
            Category Delta (Latest vs Baseline)
          </p>
          {deltaChartData.length > 0 ? (
            <BarChart
              width={380}
              height={260}
              data={deltaChartData}
              layout="vertical"
              margin={{ top: 4, right: 32, bottom: 4, left: 130 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
              <XAxis type="number" tickFormatter={(v: number) => `${v}%`} tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="category" tick={{ fontSize: 9 }} width={124} />
              <Tooltip formatter={(v: number) => [`${v}%`, 'Δ ASR']} />
              <Bar dataKey="delta" name="Δ ASR">
                {deltaChartData.map((entry, i) => (
                  <Cell key={i} fill={entry.delta > 0 ? '#ef4444' : '#22c55e'} />
                ))}
              </Bar>
            </BarChart>
          ) : (
            <p className="text-text-secondary text-sm">
              Run a second session to see category-level change.
            </p>
          )}
        </div>

        {/* Panel C: Session summary table */}
        <div className="bg-surface border border-border rounded-lg p-4 overflow-x-auto">
          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
            Session Summary
          </p>
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="bg-surface-muted">
                <th className="text-left px-2 py-1.5 font-medium text-text-secondary border-b border-border">Date</th>
                <th className="text-left px-2 py-1.5 font-medium text-text-secondary border-b border-border">Model</th>
                <th className="text-right px-2 py-1.5 font-medium text-text-secondary border-b border-border">Runs</th>
                <th className="text-right px-2 py-1.5 font-medium text-text-secondary border-b border-border">ASR</th>
                <th className="text-right px-2 py-1.5 font-medium text-text-secondary border-b border-border">Δ prev</th>
              </tr>
            </thead>
            <tbody>
              {sessionRows.map((s) => (
                <tr key={s.id} className="border-b border-border">
                  <td className="px-2 py-1.5 text-text-secondary font-mono">{s.created_at.slice(0, 10)}</td>
                  <td className="px-2 py-1.5 text-text-primary truncate max-w-28">{s.model_name}</td>
                  <td className="px-2 py-1.5 text-right text-text-secondary">{s.total_attacks}</td>
                  <td className="px-2 py-1.5 text-right text-text-primary font-mono">{(s.asr * 100).toFixed(1)}%</td>
                  <td className={`px-2 py-1.5 text-right font-mono ${
                    s.delta === null ? 'text-text-muted' : s.delta > 0 ? 'text-danger' : 'text-success'
                  }`}>
                    {s.delta === null ? '—' : `${s.delta > 0 ? '+' : ''}${(s.delta * 100).toFixed(1)}%`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Panel D: Best/worst category */}
        <div className="bg-surface border border-border rounded-lg p-4">
          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
            Category Extremes (Latest vs Baseline)
          </p>
          {bestCat && worstCat ? (
            <div className="grid grid-cols-2 gap-4">
              <StatWidget
                label="Most improved"
                value={`${(Math.abs(bestCat.delta) * 100).toFixed(1)}%`}
                subLabel={labelName(bestCat.harm_category)}
              />
              <StatWidget
                label="Most regressed"
                value={`+${(worstCat.delta * 100).toFixed(1)}%`}
                subLabel={labelName(worstCat.harm_category)}
              />
            </div>
          ) : (
            <p className="text-text-secondary text-sm">No comparison available yet.</p>
          )}
        </div>
      </div>

      <RegressionSummary model={resolvedModel} />
    </div>
  )
}
