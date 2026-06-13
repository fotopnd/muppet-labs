import { useState } from 'react'
import { useBiasResponses } from '@/hooks/useBiasResponses'

type Lang = 'zh' | 'ru' | 'ar'

const LANG_LABELS: Record<Lang, string> = { zh: 'Chinese (ZH)', ru: 'Russian (RU)', ar: 'Arabic (AR)' }

type BiasResponseViewerProps = {
  topicId: string
  model?: string | null
}

function LangBlock({ label, prompt, response }: { label: string; prompt?: string | null; response?: string | null }) {
  return (
    <div className="flex flex-col gap-2">
      <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider">{label}</p>
      {prompt ? (
        <pre className="bg-surface-muted rounded p-2 text-xs font-mono whitespace-pre-wrap break-words text-text-primary max-h-40 overflow-y-auto">
          {prompt}
        </pre>
      ) : (
        <p className="text-text-muted text-xs italic">No prompt recorded.</p>
      )}
      {response ? (
        <pre className="bg-surface-muted rounded p-2 text-xs font-mono whitespace-pre-wrap break-words text-text-primary max-h-48 overflow-y-auto">
          {response}
        </pre>
      ) : (
        <p className="text-text-muted text-xs italic">No response recorded for this language.</p>
      )}
    </div>
  )
}

export function BiasResponseViewer({ topicId, model }: BiasResponseViewerProps) {
  const [activeLang, setActiveLang] = useState<Lang>('zh')
  const { data, isLoading, isError } = useBiasResponses(topicId, model)

  if (isLoading) return <p className="text-text-secondary text-sm p-2">Loading responses…</p>
  if (isError) return <p className="text-danger text-sm p-2">Error loading responses.</p>
  if (!data) return null

  const enDetail = data.languages['en']
  const langDetail = data.languages[activeLang]

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <p className="text-sm font-semibold text-text-primary">{data.label}</p>
        <span className="text-xs text-text-muted">{data.government}</span>
        <div className="ml-auto flex gap-1">
          {(['zh', 'ru', 'ar'] as Lang[]).map((lang) => (
            <button
              key={lang}
              onClick={() => setActiveLang(lang)}
              className={`px-2 py-0.5 rounded text-xs font-mono font-medium transition-colors ${
                activeLang === lang
                  ? 'bg-accent text-text-inverse'
                  : 'bg-surface-muted text-text-secondary hover:bg-border'
              }`}
            >
              {lang.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <LangBlock
          label="English"
          prompt={enDetail?.prompt}
          response={enDetail?.response}
        />
        <LangBlock
          label={LANG_LABELS[activeLang]}
          prompt={langDetail?.prompt}
          response={langDetail?.response}
        />
        <div className="flex flex-col gap-2">
          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Back-translated</p>
          <p className="text-text-muted text-xs italic p-2 bg-surface-muted rounded">
            [Back-translation not yet available]
          </p>
        </div>
      </div>
    </div>
  )
}
