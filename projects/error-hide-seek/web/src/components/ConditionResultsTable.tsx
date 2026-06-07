import type { ConditionResult, ExperimentResults } from '@/types'

function fmtTpr(v: number | null): string {
  return v !== null ? `${(v * 100).toFixed(1)}%` : '—'
}

function fmtFpr(v: number | null): string {
  return v !== null ? `${(v * 100).toFixed(1)}%` : '—'
}

function fmtSessions(cond: ConditionResult): string {
  return cond.true_positive_rate !== null
    ? `${cond.sessions_complete} / ${cond.sessions_total}`
    : `0 / ${cond.sessions_total}`
}

function conditionLabel(c: string): string {
  if (c === 'unaided') return 'Unaided'
  if (c === 'agent_only') return 'Agent Only'
  return 'Human + Agent'
}

function categoryLabel(c: string): string {
  return c
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

const TH = 'font-interface text-xs text-text-muted uppercase tracking-wide text-left px-4 py-3 border-b border-border bg-slate-50'
const TD = 'font-data text-sm text-text-intense px-4 py-3 border-b border-border last:border-0'
const TD_LABEL = 'font-interface text-xs text-text-muted px-4 py-3 border-b border-border'

type Props = {
  results: ExperimentResults
}

export function ConditionResultsTable({ results }: Props) {
  const conditions: Record<string, ConditionResult | undefined> = {}
  for (const c of results.conditions) conditions[c.condition] = c
  const order: Array<'unaided' | 'agent_only' | 'human_agent'> = [
    'unaided',
    'agent_only',
    'human_agent',
  ]

  const allCategories = Array.from(
    new Set(results.conditions.flatMap((c) => c.by_category.map((b) => b.category))),
  )

  const uplift = results.uplift

  function tprCellClass(condKey: string): string {
    if (condKey !== 'human_agent') return TD
    if (uplift === null) return TD
    if (uplift > 0) return `${TD} bg-emerald-50 text-success font-semibold`
    if (uplift < 0) return `${TD} bg-rose-50 text-danger font-semibold`
    return TD
  }

  return (
    <div className="flex flex-col gap-0">
      <section>
        <h2 className="font-interface text-base font-semibold text-text-intense mb-4">
          Detection Rates by Condition
        </h2>
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm bg-surface">
            <thead>
              <tr>
                <th className={TH}>Metric</th>
                {order.map((c) => (
                  <th key={c} className={TH}>
                    {conditionLabel(c)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className={TD_LABEL}>True Positive Rate</td>
                {order.map((c) => (
                  <td key={c} className={tprCellClass(c)}>
                    {fmtTpr(conditions[c]?.true_positive_rate ?? null)}
                  </td>
                ))}
              </tr>
              <tr>
                <td className={TD_LABEL}>False Positive Rate</td>
                {order.map((c) => (
                  <td key={c} className={TD}>
                    {fmtFpr(conditions[c]?.false_positive_rate ?? null)}
                  </td>
                ))}
              </tr>
              <tr>
                <td className={TD_LABEL}>Sessions Complete</td>
                {order.map((c) => (
                  <td key={c} className={TD}>
                    {conditions[c] ? fmtSessions(conditions[c]!) : '—'}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {allCategories.length > 0 && (
        <section className="border-t border-border pt-8 mt-2">
          <h3 className="font-interface text-sm font-medium text-text-muted mb-4">
            By Error Category
          </h3>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm bg-surface">
              <thead>
                <tr>
                  <th className={TH}>Category</th>
                  {order.map((c) => (
                    <th key={c} className={TH}>
                      {conditionLabel(c)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {allCategories.map((cat) => (
                  <tr key={cat}>
                    <td className={TD_LABEL}>{categoryLabel(cat)}</td>
                    {order.map((c) => {
                      const cond = conditions[c]
                      const entry = cond?.by_category.find((b) => b.category === cat)
                      return (
                        <td key={c} className={TD}>
                          {entry ? fmtTpr(entry.tpr) : '—'}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  )
}
