import { useAttackSummary } from '@/hooks/useAttackSummary'
import { useStrategyComparisonByModel, MODEL_KEYS, MODEL_COLOUR, MODEL_LABEL } from '@/hooks/useStrategyComparisonByModel'
import { STRATEGY_DESCRIPTIONS } from '@/lib/strategyDescriptions'
import { StatWidget } from '@/components/StatWidget'

const WAVE_STRATEGIES = [
  'AIM', 'evil_confidant', 'few_shot_json', 'refusal_suppression', 'combination_1',
  'dev_mode_v2', 'prefix_injection', 'distractors', 'evil_system_prompt', 'multi_shot_25',
  'gcg', 'base64', 'rot13',
]

type ModelColour = 'blue' | 'orange' | 'violet'

const MODEL_BADGE_CLS: Record<ModelColour, string> = {
  blue:   'bg-blue-50 text-blue-700 ring-1 ring-blue-200',
  orange: 'bg-orange-50 text-orange-700 ring-1 ring-orange-200',
  violet: 'bg-violet-50 text-violet-700 ring-1 ring-violet-200',
}

const ASR_CLS = {
  high: 'bg-red-50 text-red-700',
  mid:  'bg-amber-50 text-amber-700',
  low:  'bg-green-50 text-green-700',
}

function ModelAsrBadge({ model, asr }: { model: string; asr: number | undefined }) {
  const colour = MODEL_COLOUR[model as keyof typeof MODEL_COLOUR] as ModelColour | undefined
  const shortName = model.split(':')[0] ?? model
  const badgeCls = colour ? MODEL_BADGE_CLS[colour] : 'bg-surface-muted text-text-muted'

  if (asr === undefined) {
    return (
      <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs ${badgeCls}`}>
        {shortName} —
      </span>
    )
  }
  const pct = (asr * 100).toFixed(0) + '%'
  const asrCls = asr >= 0.4 ? ASR_CLS.high : asr >= 0.1 ? ASR_CLS.mid : ASR_CLS.low
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium ${badgeCls}`}>
      {shortName}
      <span className={`px-1 py-0.5 rounded text-xs font-semibold ${asrCls}`}>{pct}</span>
    </span>
  )
}

export function StrategyExplorer() {
  const { byStrategy, isLoading: modelLoading } = useStrategyComparisonByModel()
  const { data: summary, isLoading: summaryLoading } = useAttackSummary()

  return (
    <div className="p-4">
      {/* Executive summary hero */}
      <div className="bg-surface border border-border rounded-lg p-5 mb-6">
        <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
          What this testbed measures
        </p>
        <p className="text-sm text-text-primary leading-relaxed mb-4">
          This platform automates adversarial safety evaluation of open-weight language models.
          It runs a corpus of known jailbreak prompts against a target model, judges each response
          with an LLM classifier (claude-haiku-4-5, 0–1 compliance score), and aggregates results
          by strategy, harm category, and model across sessions.
        </p>

        <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
          Key findings — 11,688 runs across 13 strategies and 3 models
        </p>
        <ul className="space-y-1.5 text-sm text-text-secondary">
          <li>
            <span className="text-blue-700 font-medium">gemma2:9b</span>
            {' (Google) is the most vulnerable — 31.8% avg ASR. AIM persona injection reached 55%.'}
          </li>
          <li>
            <span className="text-violet-700 font-medium">llama3.1:8b</span>
            {' (Meta) is dramatically safer — 4.0% avg ASR. AIM, base64, and few-shot all hit 0%.'}
          </li>
          <li>
            <span className="text-orange-700 font-medium">qwen2.5:7b</span>
            {' (Alibaba) sits between — 26.2% avg ASR. Resistant to persona attacks, vulnerable to prompt injection.'}
          </li>
          <li className="text-text-muted">
            Social Stereotypes is the dominant harm category across jailbreak failures.
            Persona injection is most effective; encoding obfuscation only works against weakly-aligned models.
          </li>
        </ul>
      </div>

      {/* Stat widgets */}
      <div className="grid grid-cols-3 gap-4 mb-5">
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

      {/* Model legend */}
      <div className="flex gap-2 mb-5 flex-wrap text-xs">
        {MODEL_KEYS.map((m) => {
          const colour = MODEL_COLOUR[m] as ModelColour
          return (
            <span key={m} className={`px-2 py-1 rounded font-medium ${MODEL_BADGE_CLS[colour]}`}>
              {MODEL_LABEL[m]}
            </span>
          )
        })}
        <span className="text-text-muted self-center ml-2">
          Per-card ASR badges: <span className="text-green-700">green</span> &lt;10%,{' '}
          <span className="text-amber-700">amber</span> 10–40%,{' '}
          <span className="text-red-700">red</span> ≥40%
        </span>
      </div>

      {/* Strategy cards */}
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
