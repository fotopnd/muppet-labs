import { ConditionResultsTable } from '@/components/ConditionResultsTable'
import { UpliftHero } from '@/components/UpliftHero'
import { useResults } from '@/hooks/useResults'

const EXPERIMENT_ID = 2

export function HomePage() {
  const { data: results, isLoading, isError } = useResults(EXPERIMENT_ID)

  return (
    <main className="max-w-5xl mx-auto px-6 py-8 flex flex-col gap-8">

      {/* What this is */}
      <div className="bg-surface border border-border rounded-lg p-6">
        <p className="font-interface text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
          What this testbed measures
        </p>
        <p className="font-interface text-sm text-text-primary leading-relaxed mb-3">
          Error-Hide-Seek is a scalable oversight experiment: can an LLM agent help humans find
          planted errors in academic papers, or does it introduce its own biases? Errors are
          planted by a separate LLM (claude-sonnet-4-6 across 100 papers), then human reviewers
          work under three conditions — unaided, agent-only, or human+agent — to measure whether
          AI assistance improves error detection.
        </p>
        <p className="font-interface text-sm text-text-secondary leading-relaxed">
          Key finding: agent assistance produced{' '}
          <span className="font-medium text-text-primary">near-zero uplift (−0.9% TPR)</span>
          {' '}in the human+agent condition. The agent-only condition underperformed unaided humans
          on subtle semantic errors (inverted conclusions, causal inversions) while generating more
          false positives. The agent excels at surface-level checks; humans retain an edge on
          reasoning-level errors.
        </p>
      </div>

      {/* Results */}
      {isLoading && (
        <div className="animate-pulse space-y-3">
          <div className="h-40 bg-slate-100 rounded-lg" />
          <div className="h-48 bg-slate-100 rounded-lg" />
        </div>
      )}
      {isError && (
        <p className="font-interface text-sm text-danger">Results unavailable — check API.</p>
      )}
      {results && (
        <>
          <UpliftHero uplift={results.uplift} />
          <ConditionResultsTable results={results} />
        </>
      )}

    </main>
  )
}
