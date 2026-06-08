import { useState } from 'react'
import { useDisagreements } from '@/api/metrics'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Skeleton } from '@/components/Skeleton'
import type { SourceDatasetFilter } from '@/types'

const SOURCE_OPTIONS: { value: SourceDatasetFilter; label: string }[] = [
  { value: 'wildguard', label: 'WildGuard' },
  { value: 'all', label: 'All sources' },
  { value: 'red_team', label: 'Red-team' },
]

export function Disagreements() {
  const [source, setSource] = useState<SourceDatasetFilter>('wildguard')
  const { data, isLoading, isError } = useDisagreements(source)

  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton className="h-8 w-48" />
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-14 w-full" />
        ))}
      </div>
    )
  }

  if (isError) return <ErrorMessage message="Failed to load disagreement data" />

  const samples = data?.samples ?? []
  const total = data?.total ?? 0

  return (
    <div className="flex flex-col gap-4">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-slate-900">Model Disagreements</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Events where pair classifier and taxonomy classifier contradict each other
          </p>
        </div>
        <div className="flex gap-1">
          {SOURCE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setSource(opt.value)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                source === opt.value
                  ? 'bg-slate-900 text-white'
                  : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Summary */}
      <div className="bg-white rounded-lg border border-slate-200 px-4 py-3">
        <span className="text-sm text-slate-700">
          <span className="font-semibold text-slate-900">{total.toLocaleString()}</span> total disagreements
          {samples.length < total && (
            <span className="text-slate-400 ml-1">(showing {samples.length})</span>
          )}
        </span>
      </div>

      {/* Table */}
      {samples.length === 0 ? (
        <p className="text-center text-slate-400 py-12 text-sm">No disagreements found.</p>
      ) : (
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-slate-400 text-xs uppercase tracking-wide">
                <th className="px-4 py-2 w-24">Pair</th>
                <th className="px-4 py-2">Taxonomy flags</th>
                <th className="px-4 py-2">Prompt</th>
              </tr>
            </thead>
            <tbody>
              {samples.map((s) => {
                const pairUnsafe = s.pair_label === 1
                const taxHasTags = (s.taxonomy_labels ?? []).length > 0
                // pair=unsafe but no tax tags → false alarm; pair=safe but tax tags → missed signal
                const type = pairUnsafe && !taxHasTags ? 'false-alarm' : 'missed-signal'
                return (
                  <tr key={String(s.event_id)} className="border-b border-slate-50 last:border-0">
                    <td className="px-4 py-2">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          pairUnsafe
                            ? 'bg-red-50 text-red-700'
                            : 'bg-green-50 text-green-700'
                        }`}
                      >
                        {pairUnsafe ? 'unsafe' : 'safe'}
                      </span>
                    </td>
                    <td className="px-4 py-2">
                      {taxHasTags ? (
                        <div className="flex flex-wrap gap-1">
                          {(s.taxonomy_labels ?? []).map((tag) => (
                            <span
                              key={tag}
                              className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-amber-50 text-amber-700"
                            >
                              {tag.replace(/_/g, ' ')}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-300 text-xs">none</span>
                      )}
                      <span
                        className={`ml-2 text-xs font-medium ${
                          type === 'missed-signal' ? 'text-red-500' : 'text-amber-500'
                        }`}
                      >
                        {type === 'missed-signal' ? '↑ missed' : '↓ false alarm'}
                      </span>
                    </td>
                    <td className="px-4 py-2 font-mono text-xs text-slate-500 max-w-xs truncate">
                      {s.prompt_text}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
