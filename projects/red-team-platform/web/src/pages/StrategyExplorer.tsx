import { useAttackSummary } from '@/hooks/useAttackSummary'
import { useStrategyComparisonByModel, MODEL_KEYS, MODEL_COLOUR, MODEL_LABEL } from '@/hooks/useStrategyComparisonByModel'
import { STRATEGY_DESCRIPTIONS } from '@/lib/strategyDescriptions'
import { StatWidget } from '@/components/StatWidget'

const WAVE_STRATEGIES = [
  'AIM', 'evil_confidant', 'few_shot_json', 'refusal_suppression', 'combination_1',
  'dev_mode_v2', 'prefix_injection', 'distractors', 'evil_system_prompt', 'multi_shot_25',
  'gcg', 'base64', 'rot13',
]

type ColourToken = 'danger' | 'warning' | 'success'

function ModelAsrBadge({ model, asr }: { model: string; asr: number | undefined }) {
  const colour = MODEL_COLOUR[model as keyof typeof MODEL_COLOUR] as ColourToken | undefined
  const shortName = model.split(':')[0] ?? model
  if (asr === undefined) {
    return (
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs bg-surface-muted text-text-muted">
        {shortName} —
      </span>
    )
  }
  const pct = (asr * 100).toFixed(0) + '%'
  const cls =
    colour === 'danger'  ? 'bg-danger/10 text-danger' :
    colour === 'warning' ? 'bg-warning/10 text-warning' :
                           'bg-success/10 text-success'
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-semibold ${cls}`}>
      {shortName} {pct}
    </span>
  )
}

export function StrategyExplorer() {
  const { byStrategy, isLoading: modelLoading } = useStrategyComparisonByModel()
  const { data: summary, isLoading: summaryLoading } = useAttackSummary()

  return (
    <div className="p-4">
      <div className="grid grid-cols-3 gap-4 mb-4">
        <StatWidget
          label="Total attacks"
          value={summaryLoading ? '…' : (summary?.total != null ? summary.total.toLocaleString() : '—')}
          loading={summaryLoading}
        />
        <StatWidget label="Strategies evaluated" value={13} />
        <StatWidget
          label="Models tested"
          value={3}
          subLabel="gemma2:9b · qwen2.5:7b · llama3.1:8b"
        />
      </div>

      <p className="text-xs text-text-muted mb-3">
        13 jailbreak strategies evaluated across Google (gemma2:9b), Alibaba (qwen2.5:7b), and
        Meta (llama3.1:8b). 300 attacks per strategy per model. ASR shown per model. Example templates use{' '}
        <code className="font-mono">[harmful request]</code> as a placeholder.
      </p>

      <div className="flex gap-3 mb-5 flex-wrap text-xs">
        {MODEL_KEYS.map((m) => {
          const colour = MODEL_COLOUR[m] as ColourToken
          const cls =
            colour === 'danger'  ? 'bg-danger/10 text-danger' :
            colour === 'warning' ? 'bg-warning/10 text-warning' :
                                   'bg-success/10 text-success'
          return (
            <span key={m} className={`px-2 py-1 rounded font-medium ${cls}`}>
              {MODEL_LABEL[m]}
            </span>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {WAVE_STRATEGIES.map((key) => {
          const meta = STRATEGY_DESCRIPTIONS[key]
          const modelAsrs = byStrategy[key]
          return (
            <div key={key} className="border border-border rounded-lg bg-surface p-4">
              <div className="flex items-start justify-between gap-3 mb-2">
                <div className="min-w-0">
                  <span className="font-mono text-xs text-text-muted">{key}</span>
                  <p className="text-sm font-semibold text-text-primary mt-0.5 leading-snug">
                    {meta?.label ?? key}
                  </p>
                </div>
                <div className="shrink-0 pt-0.5 flex flex-col gap-1 items-end">
                  {modelLoading ? (
                    <span className="text-xs text-text-muted">…</span>
                  ) : (
                    MODEL_KEYS.map((m) => (
                      <ModelAsrBadge key={m} model={m} asr={modelAsrs?.[m]} />
                    ))
                  )}
                </div>
              </div>

              {meta ? (
                <>
                  <p className="text-xs text-text-secondary leading-relaxed mb-3">
                    {meta.description}
                  </p>
                  <div>
                    <p className="text-xs text-text-muted uppercase tracking-wider font-semibold mb-1">
                      Example template
                    </p>
                    <code className="block bg-surface-muted rounded p-2 text-xs font-mono whitespace-pre-wrap break-words text-text-primary">
                      {meta.example}
                    </code>
                  </div>
                </>
              ) : (
                <p className="text-xs text-text-muted">No description available.</p>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
