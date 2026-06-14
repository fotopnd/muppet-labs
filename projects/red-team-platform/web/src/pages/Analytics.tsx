import { StrategyComparison } from '@/pages/StrategyComparison'
import { RegressionTracker } from '@/pages/RegressionTracker'
import { ModelComparison } from '@/components/ModelComparison'

export function Analytics() {
  return (
    <div>
      <div id="strategy" className="p-4">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Strategy Performance</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#strategy" className="text-accent hover:underline">Strategy ↑</a>
            <a href="#models" className="text-accent hover:underline">Models ↓</a>
            <a href="#runlog" className="text-accent hover:underline">Run Log ↓</a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          How each attack strategy performs against the model — success rate, volume, and category coverage.
        </p>
        <StrategyComparison />
      </div>

      <hr className="border-border mx-4" />

      <div id="models" className="p-4 mt-2">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Model Safety Comparison</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#strategy" className="text-accent hover:underline">Strategy ↑</a>
            <a href="#models" className="text-accent hover:underline">Models ↑</a>
            <a href="#runlog" className="text-accent hover:underline">Run Log ↓</a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          ASR by strategy across all three tested models — gemma2:9b, qwen2.5:7b, and llama3.1:8b.
        </p>
        <ModelComparison />
      </div>

      <hr className="border-border mx-4" />

      <div id="runlog" className="p-4 mt-2">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Run Log</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#strategy" className="text-accent hover:underline">Strategy ↑</a>
            <a href="#models" className="text-accent hover:underline">Models ↑</a>
            <a href="#runlog" className="text-accent hover:underline">Run Log ↑</a>
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
