import { StrategyComparison } from '@/pages/StrategyComparison'
import { RegressionTracker } from '@/pages/RegressionTracker'

export function Analytics() {
  return (
    <div>
      <div id="strategy" className="p-4">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Strategy Performance</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#strategy" className="text-accent hover:underline">Strategy ↑</a>
            <a href="#regression" className="text-accent hover:underline">Regression ↓</a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          How each attack strategy performs against the model — success rate, volume, and category coverage.
        </p>
        <StrategyComparison />
      </div>

      <hr className="border-border mx-4" />

      <div id="regression" className="p-4 mt-2">
        <div className="flex items-center gap-4 mb-1">
          <h2 className="text-base font-semibold text-text-primary">Regression Tracking</h2>
          <div className="flex gap-3 text-xs ml-auto">
            <a href="#strategy" className="text-accent hover:underline">Strategy ↑</a>
            <a href="#regression" className="text-accent hover:underline">Regression ↑</a>
          </div>
        </div>
        <p className="text-xs text-text-muted mb-4">
          Attack success rate across sessions — track whether model safety is improving or regressing.
        </p>
        <RegressionTracker />
      </div>
    </div>
  )
}
