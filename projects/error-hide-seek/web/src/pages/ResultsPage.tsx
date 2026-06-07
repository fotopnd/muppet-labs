import { useParams } from 'react-router-dom'

import { ConditionResultsTable } from '@/components/ConditionResultsTable'
import { UpliftHero } from '@/components/UpliftHero'
import { useResults } from '@/hooks/useResults'

export function ResultsPage() {
  const { experimentId } = useParams<{ experimentId: string }>()
  const id = experimentId ? parseInt(experimentId, 10) : null
  const { data: results, isLoading, isError } = useResults(id)

  if (isLoading) {
    return (
      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="animate-pulse space-y-2">
          <div className="h-8 bg-slate-200 rounded w-full" />
          <div className="h-8 bg-slate-200 rounded w-full" />
          <div className="h-8 bg-slate-200 rounded w-full" />
          <div className="h-8 bg-slate-200 rounded w-full" />
        </div>
      </main>
    )
  }

  if (isError || !results) {
    return (
      <main className="max-w-5xl mx-auto px-6 py-8">
        <p className="font-interface text-sm text-danger">
          Results unavailable — check API
        </p>
      </main>
    )
  }

  return (
    <main className="max-w-5xl mx-auto px-6 py-8 flex flex-col gap-8">
      <UpliftHero uplift={results.uplift} />
      <ConditionResultsTable results={results} />
    </main>
  )
}
