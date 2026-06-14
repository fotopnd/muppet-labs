import { useMemo } from 'react'
import { useCoverage } from '@/hooks/useCoverage'
import { useStrategyComparison } from '@/hooks/useStrategyComparison'
import { labelName } from '@/lib/categoryLabels'
import { STRATEGY_DESCRIPTIONS } from '@/lib/strategyDescriptions'

const BASELINE_KEYS = new Set(['none', 'original_prompt'])

export function AnalyticsSummary() {
  const { data: cmpData } = useStrategyComparison()
  const { data: covData } = useCoverage()

  const summary = useMemo(() => {
    if (!cmpData?.bars.length) return null

    const ranked = [...cmpData.bars]
      .filter((b) => !BASELINE_KEYS.has(b.strategy))
      .sort((a, b) => b.asr - a.asr)

    const best = ranked[0]
    const worst = ranked[ranked.length - 1]

    // Highest-risk category from coverage cells
    let topCategory: string | null = null
    if (covData?.cells.length) {
      const catAsr: Record<string, number[]> = {}
      for (const cell of covData.cells) {
        if (!catAsr[cell.harm_category]) catAsr[cell.harm_category] = []
        catAsr[cell.harm_category]!.push(cell.asr)
      }
      const catMeans = Object.entries(catAsr).map(([cat, asrs]) => ({
        cat,
        mean: asrs.reduce((s, v) => s + v, 0) / asrs.length,
      }))
      topCategory = catMeans.sort((a, b) => b.mean - a.mean)[0]?.cat ?? null
    }

    return { best, worst, topCategory }
  }, [cmpData, covData])

  if (!summary) return null

  const stratLabel = (key: string) =>
    STRATEGY_DESCRIPTIONS[key]?.label.split(' — ')[0] ?? key

  return (
    <div className="mt-6 bg-surface-muted rounded-lg p-4 text-sm">
      <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
        Key Findings
      </p>
      <ul className="space-y-2 text-text-primary">
        <li>
          <span className="text-text-muted">Highest-ASR strategy: </span>
          <span className="font-medium">{stratLabel(summary.best.strategy)}</span>
          {' — '}
          {(summary.best.asr * 100).toFixed(1)}% across {summary.best.total_runs} runs.
        </li>
        <li>
          <span className="text-text-muted">Lowest-ASR strategy: </span>
          <span className="font-medium">{stratLabel(summary.worst.strategy)}</span>
          {' — '}
          {(summary.worst.asr * 100).toFixed(1)}% across {summary.worst.total_runs} runs.
        </li>
        <li>
          <span className="text-text-muted">Coverage: </span>
          13 strategies × 300 runs each across 3 models (gemma2:9b, qwen2.5:7b, llama3.1:8b).
        </li>
        {summary.topCategory && (
          <li>
            <span className="text-text-muted">Highest-risk harm category across strategies: </span>
            <span className="font-medium">{labelName(summary.topCategory)}</span>.
          </li>
        )}
      </ul>
    </div>
  )
}
