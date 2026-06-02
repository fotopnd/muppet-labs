import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { ModelMetrics } from '@/types/stream'

type Props = { metrics: ModelMetrics }

function formatAccuracy(v: number | null): string {
  if (v === null) return 'N/A'
  return `${(v * 100).toFixed(1)}%`
}

function formatLatency(v: number): string {
  return `${v.toFixed(1)}ms`
}

function formatThroughput(v: number): string {
  return `${v.toFixed(2)}/s`
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between py-0.5">
      <span className="text-xs text-muted-foreground font-interface">{label}</span>
      <span className="text-sm text-foreground font-data tabular-nums">{value}</span>
    </div>
  )
}

export function ModelMetricsCard({ metrics }: Props) {
  const isPending = metrics.status === 'pending_weights'

  const badgeClass = isPending
    ? 'bg-muted text-muted-foreground hover:bg-muted'
    : 'bg-status-active-bg text-status-active-text hover:bg-status-active-bg'

  return (
    <Card className={isPending ? 'bg-muted' : 'bg-card'}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium font-interface">
            {metrics.model_name}
          </CardTitle>
          <Badge className={badgeClass}>
            {isPending ? 'Pending Weights' : 'Active'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {isPending ? (
          <p className="text-sm text-muted-foreground font-interface italic text-center py-4">
            Awaiting fine-tuned weights from project 8
          </p>
        ) : (
          <div className="space-y-1">
            <MetricRow label="Accuracy" value={formatAccuracy(metrics.accuracy)} />
            <MetricRow label="p50 latency" value={formatLatency(metrics.p50_latency_ms)} />
            <MetricRow label="p95 latency" value={formatLatency(metrics.p95_latency_ms)} />
            <MetricRow label="Throughput" value={formatThroughput(metrics.throughput_cps)} />
            <div className="pt-2 border-t border-border">
              <span className="text-xs text-muted-foreground font-data tabular-nums">
                {metrics.total_processed.toLocaleString()} processed
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
