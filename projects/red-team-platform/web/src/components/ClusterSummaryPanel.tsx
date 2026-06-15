import { useMemo } from 'react'
import { Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from 'recharts'
import { useClusters } from '@/hooks/useClusters'
import { abbrevName, categoryColour, labelName } from '@/lib/categoryLabels'
import type { ClusterSummary } from '@/types'

type BubbleDatum = {
  x: number; y: number; z: number; fill: string; cluster: ClusterSummary
}

function CustomBubble({ cx = 0, cy = 0, payload, r = 10 }: { cx?: number; cy?: number; payload?: BubbleDatum; r?: number }) {
  if (!payload) return null
  return <circle cx={cx} cy={cy} r={r} fill={payload.fill} fillOpacity={0.8} stroke={payload.fill} strokeWidth={1.5} />
}

function BubbleTooltip({ active, payload }: { active?: boolean; payload?: { payload: BubbleDatum }[] }) {
  if (!active || !payload?.length) return null
  const c = payload[0]?.payload.cluster
  if (!c) return null
  return (
    <div className="bg-canvas border border-border rounded p-2 text-xs shadow">
      <p className="font-semibold text-text-primary">Cluster {c.cluster_id}</p>
      <p className="text-text-secondary">{c.size} failures · {labelName(c.top_harm_category)}</p>
      <p className="text-text-muted font-mono">{c.top_strategy}</p>
    </div>
  )
}

export function ClusterSummaryPanel() {
  const { data, isLoading, isError } = useClusters()

  const totalFailures = useMemo(() => data?.summaries.reduce((s, c) => s + c.size, 0) ?? 0, [data])

  const { stratOrder, catOrder, bubbleData, topCallout } = useMemo(() => {
    if (!data?.summaries.length) return { stratOrder: [], catOrder: [], bubbleData: [], topCallout: null }

    const stratTotals: Record<string, number> = {}
    const catTotals: Record<string, number> = {}
    for (const c of data.summaries) {
      stratTotals[c.top_strategy] = (stratTotals[c.top_strategy] ?? 0) + c.size
      catTotals[c.top_harm_category] = (catTotals[c.top_harm_category] ?? 0) + c.size
    }
    const stratOrder = Object.entries(stratTotals).sort(([, a], [, b]) => b - a).map(([s]) => s)
    const catOrder = Object.entries(catTotals).sort(([, a], [, b]) => b - a).map(([c]) => c)

    const bubbleData: BubbleDatum[] = data.summaries.map((c) => ({
      x: stratOrder.indexOf(c.top_strategy),
      y: catOrder.indexOf(c.top_harm_category),
      z: c.size,
      fill: categoryColour(c.top_harm_category),
      cluster: c,
    }))

    const top = Object.entries(catTotals).sort(([, a], [, b]) => b - a)[0]
    const topCallout = top && totalFailures > 0
      ? { label: labelName(top[0]), pct: ((top[1] / totalFailures) * 100).toFixed(0) }
      : null

    return { stratOrder, catOrder, bubbleData, topCallout }
  }, [data, totalFailures])

  if (isLoading) return <p className="text-text-secondary text-sm">Loading…</p>
  if (isError) return <p className="text-danger text-sm">Error loading clusters.</p>
  if (!data?.summaries.length) {
    return (
      <p className="text-text-muted text-sm">
        No clusters yet — run <code className="font-mono bg-surface-muted px-1 rounded text-xs">uv run cluster</code> after an attack session.
      </p>
    )
  }

  const sorted = [...data.summaries].sort((a, b) => b.size - a.size)

  return (
    <div className="space-y-4">
      {topCallout && (
        <div className="bg-danger/5 border border-danger/20 rounded-lg px-4 py-2.5 text-sm">
          <span className="font-semibold text-danger">{topCallout.pct}%</span>
          <span className="text-text-secondary ml-1">
            of failures involve <span className="font-medium text-text-primary">{topCallout.label}</span> — the dominant harm type.
          </span>
        </div>
      )}

      <div className="bg-surface border border-border rounded-lg p-4 overflow-x-auto">
        <p className="text-xs text-text-muted mb-2">
          X = strategy (by failure volume) · Y = harm category · Bubble size = failure count · Colour = harm category
        </p>
        <ScatterChart
          width={660}
          height={260}
          margin={{ top: 12, right: 20, bottom: 40, left: 20 }}
        >
          <XAxis
            dataKey="x" type="number" name="Strategy"
            domain={[-0.5, stratOrder.length - 0.5]}
            ticks={stratOrder.map((_, i) => i)}
            tickFormatter={(i: number) => stratOrder[i] ?? ''}
            tick={{ fontSize: 9 }} angle={-30} textAnchor="end" height={55}
          />
          <YAxis
            dataKey="y" type="number" name="Harm Category"
            domain={[-0.5, catOrder.length - 0.5]}
            ticks={catOrder.map((_, i) => i)}
            tickFormatter={(i: number) => abbrevName(catOrder[i] ?? '')}
            tick={{ fontSize: 9 }} width={80}
          />
          <ZAxis dataKey="z" range={[60, 1400]} />
          <Tooltip content={<BubbleTooltip />} />
          <Scatter data={bubbleData} shape={<CustomBubble />} />
        </ScatterChart>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {sorted.map((c) => (
          <div key={c.cluster_id} className="border border-border rounded-lg p-3 bg-surface text-xs">
            <div className="flex items-center gap-1.5 mb-1.5">
              <span className="bg-accent text-text-inverse font-semibold px-1.5 py-0.5 rounded-full text-xs">
                #{c.cluster_id}
              </span>
              <span className="text-text-secondary">{c.size} failures</span>
              <span className="ml-auto text-text-muted">{((c.size / totalFailures) * 100).toFixed(0)}%</span>
            </div>
            <div className="h-1 w-full rounded-full bg-surface-muted mb-1.5">
              <div className="h-1 rounded-full bg-accent" style={{ width: `${((c.size / totalFailures) * 100).toFixed(0)}%` }} />
            </div>
            <span className="bg-surface-muted text-danger px-1 py-0.5 rounded text-xs mr-1">{labelName(c.top_harm_category)}</span>
            <span className="bg-surface-muted text-warning px-1 py-0.5 rounded text-xs font-mono">{c.top_strategy}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
