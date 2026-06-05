import type { ModelMetrics } from '@/types'
import { MetricSparkline } from './MetricSparkline'
import { StatusBadge } from './StatusBadge'

function fmt(value: number | null, decimals = 3): string {
  return value !== null ? value.toFixed(decimals) : '—'
}

type MetricCellProps = {
  label: string
  value: string
}

function MetricCell({ label, value }: MetricCellProps) {
  return (
    <div>
      <p className="font-interface text-xs text-text-muted uppercase tracking-wide">{label}</p>
      <p className="font-data text-base font-medium text-text-intense">{value}</p>
    </div>
  )
}

type ModelCardProps = {
  metrics: ModelMetrics
  sparklineData: number[]
  // Zero-shot F1 baseline for fine-tuned model cards (shown as dashed reference line)
  baselineF1?: number | null
}

export function ModelCard({ metrics, sparklineData, baselineF1 }: ModelCardProps) {
  const isPending = metrics.status === 'pending_weights' && !metrics.has_seeded_data
  const sourceBadge = metrics.source === 'live' ? 'live' : 'seeded'

  return (
    <article
      className={[
        'bg-surface rounded-lg border border-border p-5 flex flex-col gap-4',
        isPending ? 'opacity-60' : '',
      ].join(' ')}
    >
      <header className="flex items-center justify-between gap-2">
        <span className="font-interface text-sm font-semibold text-text-intense truncate">
          {metrics.display_name}
        </span>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <StatusBadge status={sourceBadge} />
          {metrics.status === 'pending_weights' && !metrics.has_seeded_data && (
            <StatusBadge status="pending_weights" />
          )}
        </div>
      </header>

      {isPending ? (
        <p className="font-interface text-sm text-text-muted text-center py-4">
          Awaiting checkpoint
        </p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-x-6 gap-y-3">
            <MetricCell label="F1" value={fmt(metrics.f1)} />
            <MetricCell label="Precision" value={fmt(metrics.precision)} />
            <MetricCell
              label="Latency p50"
              value={metrics.latency_p50 !== null ? `${metrics.latency_p50.toFixed(1)}ms` : '—'}
            />
            <MetricCell
              label="Latency p95"
              value={metrics.latency_p95 !== null ? `${metrics.latency_p95.toFixed(1)}ms` : '—'}
            />
            <div className="col-span-2">
              <MetricCell
                label="Throughput"
                value={
                  metrics.throughput_per_sec !== null
                    ? `${metrics.throughput_per_sec.toFixed(1)}/s`
                    : '—'
                }
              />
            </div>
          </div>
          <MetricSparkline
            data={sparklineData}
            label="F1 trend"
            currentValue={metrics.f1}
            baselineValue={baselineF1}
          />
        </>
      )}
    </article>
  )
}
