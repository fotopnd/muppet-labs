import { StrategyComparison } from '@/pages/StrategyComparison'
import { ModelComparison } from '@/components/ModelComparison'
import { ModelCategoryHeatmap } from '@/components/ModelCategoryHeatmap'
import { TopFailuresTable } from '@/components/TopFailuresTable'

export function Analytics() {
  return (
    <div>
      {/* Strategy Performance */}
      <div id="strategy" className="p-4">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Strategy Performance</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#models" className="text-accent hover:underline">Models ↓</a>
            <a href="#categories" className="text-accent hover:underline">Categories ↓</a>
            <a href="#failures" className="text-accent hover:underline">Failures ↓</a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          Aggregate ASR per strategy across all 3 models and 300 attacks each.
        </p>
        <StrategyComparison />
      </div>

      <hr className="border-border mx-4" />

      {/* Model Safety Comparison */}
      <div id="models" className="p-4 mt-2">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Model Safety Comparison</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#strategy" className="text-accent hover:underline">↑</a>
            <a href="#categories" className="text-accent hover:underline">Categories ↓</a>
            <a href="#failures" className="text-accent hover:underline">Failures ↓</a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          ASR by strategy broken out per model. Grouped bars show which strategies each model is most exposed to.
        </p>
        <ModelComparison />
      </div>

      <hr className="border-border mx-4" />

      {/* Model × Harm Category heatmap */}
      <div id="categories" className="p-4 mt-2">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Model × Harm Category</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#models" className="text-accent hover:underline">↑</a>
            <a href="#failures" className="text-accent hover:underline">Failures ↓</a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          Which harm categories each model is most exposed to. Ring marks the highest ASR per row.
        </p>
        <div className="bg-surface border border-border rounded-lg p-4">
          <ModelCategoryHeatmap />
        </div>
      </div>

      <hr className="border-border mx-4" />

      {/* Top Failures */}
      <div id="failures" className="p-4 mt-2">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Top Failures</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#categories" className="text-accent hover:underline">↑</a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          Highest-confidence jailbreak successes — the attacks where the model most fully complied.
          Click any row to see the full prompt and model response.
        </p>
        <TopFailuresTable />

        {/* Data provenance */}
        <div className="mt-4 bg-surface border border-border rounded-lg px-4 py-3 text-xs text-text-muted">
          <span className="font-semibold text-text-secondary">Data provenance · </span>
          11,688 runs collected June 2026 · 13 strategies × 3,900 unique prompts × 3 models ·
          harm categories assigned via RoBERTa-base taxonomy classifier (WildGuard) ·
          jailbreak success judged by <span className="font-mono">claude-haiku-4-5</span> at 0.5 threshold
        </div>
      </div>
    </div>
  )
}
