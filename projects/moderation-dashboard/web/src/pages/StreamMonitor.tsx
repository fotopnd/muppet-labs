import { AnomalyFeedItem } from '@/components/AnomalyFeedItem'
import { ErrorMessage } from '@/components/ErrorMessage'
import { FeedItemSkeleton } from '@/components/FeedItemSkeleton'
import { useAnomalyFlags, useStreamMetrics } from '@/api/stream'

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-surface rounded-lg border border-border p-5">
      <p className="font-interface text-xs text-text-muted uppercase tracking-wide">{label}</p>
      <p className="font-data text-2xl font-medium text-text-intense mt-1">{value}</p>
    </div>
  )
}

export function StreamMonitor() {
  const stream = useStreamMetrics()
  const anomalies = useAnomalyFlags()

  const totalCategories = stream.data
    ? Object.values(stream.data.category_counts).reduce((a, b) => a + b, 0)
    : 0

  return (
    <div className="space-y-6">
      {/* Stat row */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard
          label="Event rate"
          value={stream.data ? `${stream.data.event_rate_per_sec.toFixed(1)}/s` : '—'}
        />
        <StatCard
          label="Total events"
          value={stream.data ? stream.data.total_events.toLocaleString() : '—'}
        />
        <StatCard
          label="Categories (5 min)"
          value={stream.data ? String(Object.keys(stream.data.category_counts).length) : '—'}
        />
      </div>

      {/* Category breakdown */}
      <div className="bg-surface rounded-lg border border-border p-5">
        <h2 className="font-interface text-sm font-semibold text-text-intense mb-4">
          Category breakdown (last 5 min)
        </h2>
        {stream.isError ? (
          <ErrorMessage title="Failed to load stream metrics" body="Retrying automatically…" />
        ) : stream.isLoading ? (
          <p className="font-interface text-sm text-text-muted">Loading…</p>
        ) : !stream.data || totalCategories === 0 ? (
          <p className="font-interface text-sm text-text-muted">No events in the last 5 minutes</p>
        ) : (
          <ul className="space-y-2">
            {Object.entries(stream.data.category_counts)
              .sort(([, a], [, b]) => b - a)
              .map(([cat, count]) => (
                <li key={cat} className="flex items-center gap-3">
                  <span className="font-data text-sm text-text-default w-32 shrink-0">{cat}</span>
                  <div className="flex-1 bg-border rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-accent h-full rounded-full"
                      style={{ width: `${(count / totalCategories) * 100}%` }}
                    />
                  </div>
                  <span className="font-data text-sm text-text-muted w-12 text-right">{count}</span>
                </li>
              ))}
          </ul>
        )}
      </div>

      {/* Anomaly feed */}
      <div className="bg-surface rounded-lg border border-border p-5">
        <h2 className="font-interface text-sm font-semibold text-text-intense mb-4">
          Anomaly feed
        </h2>
        {anomalies.isError ? (
          <ErrorMessage title="Failed to load anomalies" body="Retrying automatically…" />
        ) : anomalies.isLoading ? (
          <ul>
            {[0, 1, 2].map(i => (
              <FeedItemSkeleton key={i} />
            ))}
          </ul>
        ) : !anomalies.data || anomalies.data.length === 0 ? (
          <p className="font-interface text-sm text-text-muted py-4 text-center">
            No anomalies detected
          </p>
        ) : (
          <ul>
            {anomalies.data.map(flag => (
              <AnomalyFeedItem key={flag.id} flag={flag} />
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
