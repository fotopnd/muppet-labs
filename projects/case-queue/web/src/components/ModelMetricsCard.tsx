import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  YAxis,
} from 'recharts'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { HistoryPoint, ModelMetrics } from '@/types/stream'

type Props = { metrics: ModelMetrics; history: HistoryPoint[] }

function fmt(v: number | null, unit: string, scale = 1): string {
  if (v === null) return 'N/A'
  return `${(v * scale).toFixed(unit === '%' ? 1 : 2)}${unit}`
}

function MetricRow({ label, value, dimmed }: { label: string; value: string; dimmed?: boolean }) {
  return (
    <div className="flex items-baseline justify-between py-0.5">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className={`text-sm tabular-nums ${dimmed ? 'text-muted-foreground' : 'text-foreground'}`}>
        {value}
      </span>
    </div>
  )
}

function AccuracyChart({ data }: { data: HistoryPoint[] }) {
  if (data.length < 2) return <div className="h-16 flex items-center justify-center text-xs text-muted-foreground">Waiting for data…</div>
  return (
    <ResponsiveContainer width="100%" height={64}>
      <LineChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
        <YAxis domain={[0, 1]} hide />
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const v = payload[0]?.value as number | null
            return (
              <div className="rounded border border-border bg-popover px-2 py-1 text-xs shadow-sm">
                <span className="text-muted-foreground">{(payload[0]?.payload as HistoryPoint).t} </span>
                <span className="font-medium">{v === null ? 'N/A' : `${(v * 100).toFixed(1)}%`}</span>
              </div>
            )
          }}
        />
        <Line
          type="monotone"
          dataKey="accuracy"
          stroke="hsl(var(--primary))"
          strokeWidth={1.5}
          dot={false}
          connectNulls={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

function LatencyChart({ data }: { data: HistoryPoint[] }) {
  if (data.length < 2) return <div className="h-16 flex items-center justify-center text-xs text-muted-foreground">Waiting for data…</div>
  return (
    <ResponsiveContainer width="100%" height={64}>
      <LineChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
        <YAxis hide />
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const pt = payload[0]?.payload as HistoryPoint
            return (
              <div className="rounded border border-border bg-popover px-2 py-1 text-xs shadow-sm space-y-0.5">
                <div className="text-muted-foreground">{pt.t}</div>
                <div><span className="text-blue-500">p50</span> {pt.p50.toFixed(1)}ms</div>
                <div><span className="text-orange-400">p95</span> {pt.p95.toFixed(1)}ms</div>
              </div>
            )
          }}
        />
        <Line type="monotone" dataKey="p50" stroke="hsl(217 91% 60%)" strokeWidth={1.5} dot={false} name="p50" />
        <Line type="monotone" dataKey="p95" stroke="hsl(38 92% 50%)" strokeWidth={1.5} dot={false} name="p95" strokeDasharray="4 2" />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function ModelMetricsCard({ metrics, history }: Props) {
  const isPending = metrics.status === 'pending_weights'

  const badgeClass = isPending
    ? 'bg-muted text-muted-foreground hover:bg-muted'
    : 'bg-status-active-bg text-status-active-text hover:bg-status-active-bg'

  return (
    <Card className={isPending ? 'bg-muted' : 'bg-card'}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">{metrics.model_name}</CardTitle>
          <Badge className={badgeClass}>{isPending ? 'Pending Weights' : 'Active'}</Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {isPending ? (
          <p className="text-sm text-muted-foreground italic text-center py-4">
            Awaiting fine-tuned weights from project 8
          </p>
        ) : (
          <div className="space-y-1">
            <MetricRow label="Accuracy" value={fmt(metrics.accuracy, '%', 100)} dimmed={metrics.accuracy === null} />
            <MetricRow label="p50 latency" value={`${metrics.p50_latency_ms.toFixed(1)}ms`} />
            <MetricRow label="p95 latency" value={`${metrics.p95_latency_ms.toFixed(1)}ms`} />
            <MetricRow label="Throughput" value={`${metrics.throughput_cps.toFixed(2)}/s`} />

            <div className="pt-2 space-y-2">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Accuracy</p>
                <AccuracyChart data={history} />
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">
                  Latency <span className="text-blue-500">p50</span> / <span className="text-orange-400">p95</span>
                </p>
                <LatencyChart data={history} />
              </div>
            </div>

            <div className="pt-2 border-t border-border">
              <span className="text-xs text-muted-foreground tabular-nums">
                {metrics.total_processed.toLocaleString()} processed
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
