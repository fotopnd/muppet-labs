import { useState } from 'react'
import { useBiasResponses } from '@/hooks/useBiasResponses'

type Lang = 'zh' | 'ru' | 'ar'

const LANG_LABELS: Record<Lang, string> = { zh: 'Chinese (ZH)', ru: 'Russian (RU)', ar: 'Arabic (AR)' }

type BiasResponseViewerProps = {
  topicId: string
  model?: string | null
}

function TextBlock({ label, content, muted = false }: { label: string; content?: string | null; muted?: boolean }) {
  return (
    <div className="flex flex-col gap-2">
      <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider">{label}</p>
      {content ? (
        <pre className={`rounded p-2 text-xs font-mono whitespace-pre-wrap break-words text-text-primary max-h-48 overflow-y-auto ${muted ? 'bg-accent-subtle border border-border' : 'bg-surface-muted'}`}>
          {content}
        </pre>
      ) : (
        <p className="text-text-muted text-xs italic p-2 bg-surface-muted rounded">—</p>
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

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <TextBlock label="English response" content={enDetail?.response ?? null} />
        <TextBlock label={`${LANG_LABELS[activeLang]} response`} content={langDetail?.response ?? null} />
        <TextBlock
          label="Back-translated (EN)"
          content={langDetail?.back_translation ?? null}
          muted
        />
        <div className="flex flex-col gap-2">
          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Cosine distance</p>
          {langDetail?.cosine_distance != null ? (
            <div className="p-2 bg-surface-muted rounded">
              <span className={`text-2xl font-mono font-bold ${
                langDetail.cosine_distance >= 0.9 ? 'text-red-600' :
                langDetail.cosine_distance >= 0.6 ? 'text-orange-500' :
                langDetail.cosine_distance >= 0.3 ? 'text-amber-500' : 'text-green-600'
              }`}>
                {langDetail.cosine_distance.toFixed(2)}
              </span>
              <p className="text-xs text-text-muted mt-1">
                {langDetail.cosine_distance >= 0.9
                  ? 'Strongly divergent from English'
                  : langDetail.cosine_distance >= 0.6
                  ? 'Moderately divergent'
                  : langDetail.cosine_distance >= 0.3
                  ? 'Slightly divergent'
                  : 'Close to English response'}
              </p>
            </div>
          ) : (
            <p className="text-text-muted text-xs italic p-2 bg-surface-muted rounded">—</p>
          )}
        </div>
      </div>
    </div>
  )
}
