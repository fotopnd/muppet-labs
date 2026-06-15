import { StrategyComparison } from '@/pages/StrategyComparison'
import { RegressionTracker } from '@/pages/RegressionTracker'
import { ModelComparison } from '@/components/ModelComparison'
import { ModelCategoryHeatmap } from '@/components/ModelCategoryHeatmap'
import { ClusterSummaryPanel } from '@/components/ClusterSummaryPanel'

export function Analytics() {
  return (
    <div>
      {/* Strategy Performance */}
      <div id="strategy" className="p-4">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Strategy Performance</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#strategy" className="text-accent hover:underline">Strategy ↑</a>
            <a href="#models" className="text-accent hover:underline">Models ↓</a>
            <a href="#categories" className="text-accent hover:underline">Categories ↓</a>
            <a href="#clusters" className="text-accent hover:underline">Clusters ↓</a>
            <a href="#runlog" className="text-accent hover:underline">Run Log ↓</a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          How each attack strategy performs — success rate, volume, and category coverage.
        </p>
        <StrategyComparison />
      </div>

      <hr className="border-border mx-4" />

      {/* Model Safety Comparison — per strategy */}
      <div id="models" className="p-4 mt-2">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Model Safety Comparison</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#strategy" className="text-accent hover:underline">↑</a>
            <a href="#categories" className="text-accent hover:underline">Categories ↓</a>
            <a href="#clusters" className="text-accent hover:underline">Clusters ↓</a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          ASR by strategy across all three models. Bars per strategy group show model differences directly.
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
            <a href="#clusters" className="text-accent hover:underline">Clusters ↓</a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          Aggregate ASR per harm category per model. Shows which harm types each model is most exposed to.
        </p>
        <div className="bg-surface border border-border rounded-lg p-4">
          <ModelCategoryHeatmap />
        </div>
      </div>

      <hr className="border-border mx-4" />

      {/* Failure Clusters */}
      <div id="clusters" className="p-4 mt-2">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Failure Patterns</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#categories" className="text-accent hover:underline">↑</a>
            <a href="#runlog" className="text-accent hover:underline">Run Log ↓</a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          K-means clusters over jailbreak embeddings — groups semantically similar failures.
          Bubble size = cluster size; colour = dominant harm category.
        </p>
        <ClusterSummaryPanel />
      </div>

      <hr className="border-border mx-4" />

      {/* Run Log */}
      <div id="runlog" className="p-4 mt-2">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Run Log</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#strategy" className="text-accent hover:underline">↑ Top</a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          Per-session attack results. All runs were executed on the same date — regression tracking requires multiple sessions over time.
        </p>
        <RegressionTracker />
      </div>
    </div>
  )
}
