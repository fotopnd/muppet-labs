import { useDisagreements } from '@/api/shadow'
import type { DisagreementSample, DisagreementVerdict } from '@/types'

function VerdictBadge({ verdict }: { verdict: DisagreementVerdict }) {
  const label = verdict.predicted_label === 1 ? 'Toxic' : 'Clean'
  const pct = (verdict.confidence * 100).toFixed(0)
  const colour =
    verdict.predicted_label === 1
      ? 'bg-red-900/40 text-red-300'
      : 'bg-green-900/40 text-green-300'
  return (
    <span
      className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 font-data text-xs ${colour}`}
    >
      <span className="font-interface text-xs text-text-muted">{verdict.model_name}</span>
      {label} {pct}%
    </span>
  )
}

function SamplePost({ sample }: { sample: DisagreementSample }) {
  return (
    <li className="rounded border border-border bg-surface p-3 flex flex-col gap-2">
      <p className="font-data text-sm text-text-intense leading-snug">{sample.content}</p>
      <div className="flex flex-wrap gap-1.5">
        {sample.verdicts.map(v => (
          <VerdictBadge key={v.model_name} verdict={v} />
        ))}
      </div>
    </li>
  )
}

export function DisagreementPanel() {
  const { data, isLoading, isError } = useDisagreements()

  if (isError) {
    return (
      <section className="mt-6 rounded-lg border border-border bg-surface p-5">
        <p className="font-interface text-sm text-text-muted">
          Failed to load disagreement data. Retrying automatically…
        </p>
      </section>
    )
  }

  return (
    <section className="mt-6 rounded-lg border border-border bg-surface p-5 flex flex-col gap-5">
      <header className="flex items-baseline justify-between">
        <h3 className="font-interface text-sm font-semibold text-text-intense">
          Model Disagreements — Last Hour
        </h3>
        {!isLoading && data && (
          <span className="font-data text-2xl font-semibold text-text-intense">
            {data.total_last_hour}
          </span>
        )}
      </header>

      {isLoading || !data ? (
        <div className="h-4 w-32 rounded bg-border animate-pulse" />
      ) : (
        <>
          {Object.keys(data.by_category).length > 0 && (
            <div>
              <p className="font-interface text-xs text-text-muted uppercase tracking-wide mb-2">
                By category
              </p>
              <table className="w-full text-sm">
                <tbody>
                  {Object.entries(data.by_category)
                    .sort(([, a], [, b]) => b - a)
                    .map(([cat, cnt]) => (
                      <tr key={cat} className="border-t border-border">
                        <td className="py-1.5 font-interface text-text-intense capitalize">
                          {cat}
                        </td>
                        <td className="py-1.5 font-data text-right text-text-intense">{cnt}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}

          {data.samples.length > 0 && (
            <div>
              <p className="font-interface text-xs text-text-muted uppercase tracking-wide mb-2">
                Sample posts
              </p>
              <ul className="flex flex-col gap-2">
                {data.samples.map(s => (
                  <SamplePost key={s.event_id} sample={s} />
                ))}
              </ul>
            </div>
          )}

          {data.total_last_hour === 0 && (
            <p className="font-interface text-sm text-text-muted">
              No model disagreements in the last hour.
            </p>
          )}
        </>
      )}
    </section>
  )
}
