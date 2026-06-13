import { useRef, useState } from 'react'
import { Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from 'recharts'
import { useClusters, useClusterMembers } from '@/hooks/useClusters'
import { abbrevName, categoryColour, labelName } from '@/lib/categoryLabels'
import type { ClusterSummary } from '@/types'

type BubbleDatum = {
  x: number
  y: number
  z: number
  fill: string
  cluster: ClusterSummary
}

type CustomDotProps = {
  cx?: number
  cy?: number
  payload?: BubbleDatum
  r?: number
}

function CustomBubble(props: CustomDotProps) {
  const { cx = 0, cy = 0, payload, r = 10 } = props
  if (!payload) return null
  return (
    <circle
      cx={cx}
      cy={cy}
      r={r}
      fill={payload.fill}
      fillOpacity={0.8}
      stroke={payload.fill}
      strokeWidth={1.5}
    />
  )
}

type BubbleTooltipProps = {
  active?: boolean
  payload?: { payload: BubbleDatum }[]
}

function BubbleTooltip({ active, payload }: BubbleTooltipProps) {
  if (!active || !payload?.length) return null
  const c = payload[0]?.payload.cluster
  if (!c) return null
  return (
    <div className="bg-canvas border border-border rounded p-2 text-xs shadow">
      <p className="font-semibold text-text-primary">Cluster {c.cluster_id}</p>
      <p className="text-text-secondary">{c.size} failures</p>
      <p className="text-text-secondary">{labelName(c.top_harm_category)}</p>
      <p className="text-text-secondary font-mono">{c.top_strategy}</p>
    </div>
  )
}

export function FailureClusters() {
  const [highlightedId, setHighlightedId] = useState<number | null>(null)
  const [expandedClusterId, setExpandedClusterId] = useState<number | null>(null)
  const { data, isLoading, isError } = useClusters()
  const { data: members, isLoading: membersLoading } = useClusterMembers(expandedClusterId)
  const cardRefs = useRef<Record<number, HTMLDivElement | null>>({})

  if (isLoading) return <p className="p-4 text-text-secondary text-sm">Loading…</p>
  if (isError) return <p className="p-4 text-danger text-sm">Error loading clusters.</p>
  if (!data || data.summaries.length === 0) {
    return (
      <p className="p-4 text-text-muted text-sm">
        No failure clusters yet. Run{' '}
        <code className="font-mono bg-surface-muted px-1 rounded text-xs">uv run cluster</code>{' '}
        after an attack session.
      </p>
    )
  }

  const totalFailures = data.summaries.reduce((s, c) => s + c.size, 0)

  // Build categorical axes: strategy (X) and harm category (Y)
  // sorted by total cluster size for each group descending
  const stratTotals: Record<string, number> = {}
  const catTotals: Record<string, number> = {}
  for (const c of data.summaries) {
    stratTotals[c.top_strategy] = (stratTotals[c.top_strategy] ?? 0) + c.size
    catTotals[c.top_harm_category] = (catTotals[c.top_harm_category] ?? 0) + c.size
  }
  const stratOrder = Object.entries(stratTotals)
    .sort(([, a], [, b]) => b - a)
    .map(([s]) => s)
  const catOrder = Object.entries(catTotals)
    .sort(([, a], [, b]) => b - a)
    .map(([c]) => c)

  const bubbleData: BubbleDatum[] = data.summaries.map((c) => ({
    x: stratOrder.indexOf(c.top_strategy),
    y: catOrder.indexOf(c.top_harm_category),
    z: c.size,
    fill: categoryColour(c.top_harm_category),
    cluster: c,
  }))

  // Cards sorted by % of all failures descending
  const sortedSummaries = [...data.summaries].sort((a, b) => b.size - a.size)

  function handleBubbleClick(datum: BubbleDatum) {
    const id = datum.cluster.cluster_id
    setHighlightedId(id)
    setExpandedClusterId(id)
    cardRefs.current[id]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }

  return (
    <div className="p-4">
      <h2 className="text-base font-semibold text-text-primary mb-4">Failure Clusters</h2>

      {/* Bubble chart */}
      <div className="bg-surface border border-border rounded-lg p-4 mb-6 overflow-x-auto">
        <p className="text-xs text-text-muted mb-2">
          X = attack strategy (by failure volume) · Y = harm category (by failure volume) ·
          Bubble size = failure count · Colour = harm category · Click to expand
        </p>
        <ScatterChart
          width={680}
          height={300}
          margin={{ top: 16, right: 20, bottom: 40, left: 20 }}
          onClick={(state) => {
            if (state?.activePayload?.[0]?.payload) {
              handleBubbleClick(state.activePayload[0].payload as BubbleDatum)
            }
          }}
        >
          <XAxis
            dataKey="x"
            type="number"
            name="Strategy"
            domain={[-0.5, stratOrder.length - 0.5]}
            ticks={stratOrder.map((_, i) => i)}
            tickFormatter={(i: number) => stratOrder[i] ?? ''}
            tick={{ fontSize: 9 }}
            angle={-30}
            textAnchor="end"
            height={60}
            label={{ value: 'Strategy (sorted by failure volume)', position: 'insideBottom', offset: -30, fontSize: 10 }}
          />
          <YAxis
            dataKey="y"
            type="number"
            name="Harm Category"
            domain={[-0.5, catOrder.length - 0.5]}
            ticks={catOrder.map((_, i) => i)}
            tickFormatter={(i: number) => abbrevName(catOrder[i] ?? '')}
            tick={{ fontSize: 9 }}
            width={90}
            label={{ value: 'Harm Category', angle: -90, position: 'insideLeft', offset: 10, fontSize: 10 }}
          />
          <ZAxis dataKey="z" range={[60, 1600]} />
          <Tooltip content={<BubbleTooltip />} />
          <Scatter
            data={bubbleData}
            shape={<CustomBubble />}
            style={{ cursor: 'pointer' }}
          />
        </ScatterChart>
      </div>

      {/* Card grid — sorted by % of failures */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sortedSummaries.map((c) => (
          <div
            key={c.cluster_id}
            ref={(el) => { cardRefs.current[c.cluster_id] = el }}
            className={`border rounded-lg p-3 bg-surface transition-shadow ${
              highlightedId === c.cluster_id ? 'ring-2 ring-accent border-accent' : 'border-border'
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="bg-accent text-text-inverse text-xs font-semibold px-2 py-0.5 rounded-full">
                Cluster {c.cluster_id}
              </span>
              <span className="text-text-secondary text-sm">{c.size} failures</span>
              <span className="ml-auto text-xs text-text-muted font-mono">
                {(c.size / totalFailures * 100).toFixed(1)}%
              </span>
            </div>

            <div className="flex gap-1.5 flex-wrap mb-2">
              <span className="bg-surface-muted text-danger text-xs px-1.5 py-0.5 rounded">
                {labelName(c.top_harm_category)}
              </span>
              <span className="bg-surface-muted text-warning text-xs px-1.5 py-0.5 rounded font-mono">
                {c.top_strategy}
              </span>
            </div>

            <code className="block bg-surface-muted rounded p-2 text-xs font-mono whitespace-pre-wrap break-words text-text-primary mb-2">
              {c.representative_text.slice(0, 120)}{c.representative_text.length > 120 ? '…' : ''}
            </code>

            {/* Proportion bar */}
            <div className="h-1.5 w-full rounded-full bg-surface-muted mb-2">
              <div
                className="h-1.5 rounded-full bg-accent"
                style={{ width: `${(c.size / totalFailures * 100).toFixed(1)}%` }}
              />
            </div>

            <button
              onClick={() => setExpandedClusterId(expandedClusterId === c.cluster_id ? null : c.cluster_id)}
              className="text-xs text-accent hover:text-accent-hover font-medium"
            >
              {expandedClusterId === c.cluster_id ? 'Hide members' : 'Show members'}
            </button>
          </div>
        ))}
      </div>

      {/* Member table */}
      {expandedClusterId !== null && (
        <div className="mt-6 border border-border rounded-lg p-4 bg-surface">
          <div className="flex justify-between items-center mb-3">
            <p className="text-sm font-semibold text-text-primary">Cluster {expandedClusterId} members</p>
            <button
              onClick={() => setExpandedClusterId(null)}
              className="text-text-muted hover:text-text-primary text-lg leading-none"
            >
              ×
            </button>
          </div>

          {membersLoading && <p className="text-text-secondary text-sm">Loading members…</p>}

          {members && (
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="bg-surface-muted">
                  <th className="text-left px-2 py-1.5 font-medium text-text-secondary border-b border-border">Attack Text</th>
                  <th className="text-left px-2 py-1.5 font-medium text-text-secondary border-b border-border">Category</th>
                  <th className="text-left px-2 py-1.5 font-medium text-text-secondary border-b border-border">Strategy</th>
                  <th className="text-right px-2 py-1.5 font-medium text-text-secondary border-b border-border">Score</th>
                  <th className="text-right px-2 py-1.5 font-medium text-text-secondary border-b border-border">Latency</th>
                </tr>
              </thead>
              <tbody>
                {members.members.map((m) => (
                  <tr key={m.run_id} className="border-b border-border">
                    <td className="px-2 py-1.5 text-text-primary">{m.attack_text.slice(0, 80)}…</td>
                    <td className="px-2 py-1.5 text-text-secondary">{labelName(m.harm_category)}</td>
                    <td className="px-2 py-1.5 text-text-secondary font-mono">{m.strategy}</td>
                    <td className="px-2 py-1.5 text-right font-mono text-text-secondary">{m.classifier_score.toFixed(2)}</td>
                    <td className="px-2 py-1.5 text-right text-text-muted">{m.latency_ms}ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}
