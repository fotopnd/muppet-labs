import { useMemo } from 'react'
import { useCategoryDelta } from '@/hooks/useCategoryDelta'
import { useRegression } from '@/hooks/useRegression'
import { labelName } from '@/lib/categoryLabels'

type Props = { model: string | null }

export function RegressionSummary({ model }: Props) {
  const { data: regData } = useRegression()
  const { data: deltaData } = useCategoryDelta(model)

  const summary = useMemo(() => {
    if (!regData?.points.length) return null

    const resolvedModel = model ?? regData.model_names[0] ?? null
    const modelPoints = regData.points
      .filter((p) => p.model_name === resolvedModel)
      .sort((a, b) => a.created_at.localeCompare(b.created_at))

    if (modelPoints.length === 0) return null

    const baseline = modelPoints[0]!
    const latest = modelPoints[modelPoints.length - 1]!
    const singleSession = modelPoints.length === 1

    const delta = singleSession ? null : latest.asr - baseline.asr

    const worstCat = deltaData?.items.length
      ? [...deltaData.items].sort((a, b) => b.delta - a.delta)[0] ?? null
      : null
    const bestCat = deltaData?.items.length
      ? [...deltaData.items].sort((a, b) => a.delta - b.delta)[0] ?? null
      : null

    return { baseline, latest, delta, singleSession, worstCat, bestCat, resolvedModel }
  }, [regData, deltaData, model])

  if (!summary) return null

  const pct = (v: number) => `${(v * 100).toFixed(1)}%`
  const sign = (v: number) => (v >= 0 ? '+' : '')

  return (
    <div className="mt-6 bg-surface-muted rounded-lg p-4 text-sm">
      <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
        Regression Summary
      </p>
      <ul className="space-y-2 text-text-primary">
        {summary.singleSession ? (
          <li className="text-text-muted italic">
            Only one session recorded — run a second attack session to track change over time.
          </li>
        ) : (
          <>
            <li>
              <span className="text-text-muted">Latest session: </span>
              <span className="font-medium">{pct(summary.latest.asr)} ASR</span>
              {summary.delta !== null && (
                <span
                  className={`ml-2 font-mono text-xs ${
                    summary.delta > 0 ? 'text-danger' : 'text-success'
                  }`}
                >
                  ({sign(summary.delta)}{pct(summary.delta)} vs baseline)
                </span>
              )}
            </li>
            {summary.worstCat && summary.worstCat.delta > 0 && (
              <li>
                <span className="text-text-muted">Most regressed category: </span>
                <span className="font-medium text-danger">
                  {labelName(summary.worstCat.harm_category)}
                </span>
                {' (+'}
                {pct(summary.worstCat.delta)}
                {' ASR since baseline)'}
              </li>
            )}
            {summary.bestCat && summary.bestCat.delta < 0 && (
              <li>
                <span className="text-text-muted">Most improved category: </span>
                <span className="font-medium text-success">
                  {labelName(summary.bestCat.harm_category)}
                </span>
                {' ('}
                {pct(summary.bestCat.delta)}
                {' ASR since baseline)'}
              </li>
            )}
          </>
        )}
      </ul>
    </div>
  )
}
