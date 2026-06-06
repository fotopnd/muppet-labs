import { useDisagreements } from '@/api/metrics'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Skeleton } from '@/components/Skeleton'

export function ModelComparison() {
  const { data, isLoading, isError } = useDisagreements()

  if (isLoading) return <Skeleton className="h-40 w-full" />
  if (isError) return <ErrorMessage message="Failed to load disagreement data" />

  const samples = data?.samples ?? []

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-500">
        Events where pair classifier and taxonomy classifier disagree:{' '}
        <span className="font-medium text-gray-800">{data?.total ?? 0}</span>
      </p>
      <div className="space-y-2">
        {samples.map((s) => (
          <div key={s.event_id} className="border border-gray-200 rounded p-3 text-sm">
            <p className="text-gray-800 mb-1">{s.prompt_text}</p>
            <div className="flex gap-3 text-xs text-gray-500">
              <span>Pair: {s.pair_label === 1 ? '⚠ Unsafe' : '✓ Safe'}</span>
              <span>Taxonomy: {(s.taxonomy_labels?.length ?? 0) > 0 ? s.taxonomy_labels!.join(', ') : 'none'}</span>
            </div>
          </div>
        ))}
        {samples.length === 0 && (
          <p className="text-center text-gray-400 py-12">No disagreements detected yet.</p>
        )}
      </div>
    </div>
  )
}
