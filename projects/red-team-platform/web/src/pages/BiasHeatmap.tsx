import { Fragment, useEffect, useMemo, useState } from 'react'
import { useBiasScoresMulti } from '@/hooks/useBiasScoresMulti'
import { BiasResponseViewer } from '@/components/BiasResponseViewer'

type LangKey = 'zh' | 'ru' | 'ar'
const LANGUAGES: { key: LangKey; label: string }[] = [
  { key: 'zh', label: 'ZH — Chinese' },
  { key: 'ru', label: 'RU — Russian' },
  { key: 'ar', label: 'AR — Arabic' },
]

const MODEL_HDR_CLS: Record<string, string> = {
  'gemma2:9b':    'text-blue-700',
  'qwen2.5:7b':  'text-orange-700',
  'llama3.1:8b': 'text-violet-700',
}
const MODEL_SHORT: Record<string, string> = {
  'gemma2:9b':    'gemma2',
  'qwen2.5:7b':  'qwen2.5',
  'llama3.1:8b': 'llama3.1',
}

function scoreCell(score: number | null | undefined, isMax: boolean) {
  if (score === null || score === undefined) {
    return (
      <span className="inline-flex items-center justify-center w-14 h-7 rounded text-xs font-mono text-text-muted bg-surface-muted">
        —
      </span>
    )
  }
  const bg =
    score >= 0.9 ? 'bg-red-200 text-red-900' :
    score >= 0.6 ? 'bg-orange-100 text-orange-900' :
    score >= 0.3 ? 'bg-amber-50 text-amber-900' :
                   'bg-green-50 text-green-900'
  return (
    <span className={`inline-flex items-center justify-center w-14 h-7 rounded text-xs font-mono font-semibold ${bg} ${isMax ? 'ring-2 ring-red-400' : ''}`}>
      {score.toFixed(2)}
    </span>
  )
}

export function BiasHeatmap() {
  const { data, isLoading, isError } = useBiasScoresMulti()
  const [lang, setLang] = useState<LangKey>('zh')
  const [govFilter, setGovFilter] = useState('')
  const [topicFilter, setTopicFilter] = useState('')
  const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null)

  const models = data?.available_models ?? []

  // Build lookup: topic_id → model_name → {zh,ru,ar}
  const lookup = useMemo(() => {
    const m: Record<string, Record<string, Record<LangKey, number | null>>> = {}
    for (const row of data?.rows ?? []) {
      if (!m[row.topic_id]) m[row.topic_id] = {}
      m[row.topic_id]![row.model_name] = {
        zh: row.zh_score,
        ru: row.ru_score,
        ar: row.ar_score,
      }
    }
    return m
  }, [data])

  // Unique topics with metadata
  const topics = useMemo(() => {
    const seen = new Set<string>()
    const out: { topic_id: string; government: string; label: string }[] = []
    for (const row of data?.rows ?? []) {
      if (!seen.has(row.topic_id)) {
        seen.add(row.topic_id)
        out.push({ topic_id: row.topic_id, government: row.government, label: row.label })
      }
    }
    return out
  }, [data])

  const filtered = useMemo(() => {
    return topics
      .filter((t) => !govFilter || t.government === govFilter)
      .filter((t) => !topicFilter || t.label.toLowerCase().includes(topicFilter.toLowerCase()))
  }, [topics, govFilter, topicFilter])

  const governments = useMemo(
    () => ['', ...Array.from(new Set(topics.map((t) => t.government))).sort()],
    [topics],
  )

  useEffect(() => {
    if (selectedTopicId && !filtered.some((t) => t.topic_id === selectedTopicId)) {
      setSelectedTopicId(null)
    }
  }, [filtered, selectedTopicId])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') setSelectedTopicId(null) }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  if (isLoading) return <p className="p-4 text-text-secondary text-sm">Loading bias scores…</p>
  if (isError) return <p className="p-4 text-danger text-sm">Error loading bias scores.</p>

  if (!data || data.rows.length === 0)
    return (
      <div className="p-4">
        <h2 className="mb-2 text-base font-semibold text-text-primary">Language Bias Heatmap</h2>
        <p className="text-text-muted text-sm">
          No scores yet. Run{' '}
          <code className="font-mono bg-surface-muted px-1 rounded text-xs">seed-bias-corpus</code>{' '}
          then{' '}
          <code className="font-mono bg-surface-muted px-1 rounded text-xs">attack --mode bias --language &lt;lang&gt;</code>{' '}
          then{' '}
          <code className="font-mono bg-surface-muted px-1 rounded text-xs">score-bias</code>.
        </p>
      </div>
    )

  // Group filtered topics by government
  const groups = Array.from(
    filtered.reduce((acc, t) => {
      const list = acc.get(t.government) ?? []
      list.push(t)
      acc.set(t.government, list)
      return acc
    }, new Map<string, typeof filtered>()),
  )

  return (
    <div className="p-4">
      <div className="mb-3 flex items-center justify-between flex-wrap gap-2">
        <h2 className="text-base font-semibold text-text-primary">Language Bias Heatmap</h2>
        <span className="text-xs text-text-muted">
          {models.length} model{models.length !== 1 ? 's' : ''} scored
        </span>
      </div>

      {/* Topline summary */}
      <div className="bg-surface border border-border rounded-lg p-4 mb-4 text-sm">
        <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
          What this measures
        </p>
        <p className="text-text-secondary leading-relaxed mb-2">
          Each row is a geopolitically sensitive topic. For each language column, the score is the
          cosine distance between the model's English response and its response in that language.
          Higher = more divergent. Select a language tab to compare models side-by-side.
        </p>
        <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1 mt-3">
          Key finding (gemma2:9b, all languages)
        </p>
        <ul className="space-y-1 text-text-secondary text-xs">
          <li>Average divergence 0.83–0.89 across ZH/RU/AR — responses consistently differ from English.</li>
          <li>1.00 spikes on contested sovereignty topics: Taiwan, South China Sea, Jerusalem, Gaza.</li>
          <li>Click any row to see side-by-side responses with back-translation.</li>
        </ul>
      </div>

      {/* Language selector */}
      <div className="flex gap-1 mb-4">
        {LANGUAGES.map((l) => (
          <button
            key={l.key}
            onClick={() => setLang(l.key)}
            className={`px-3 py-1.5 text-xs font-medium rounded border transition-colors ${
              lang === l.key
                ? 'bg-accent text-text-inverse border-accent'
                : 'border-border text-text-secondary hover:text-text-primary bg-surface'
            }`}
          >
            {l.label}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-4 flex-wrap">
        <select
          value={govFilter}
          onChange={(e) => setGovFilter(e.target.value)}
          className="px-2 py-1 text-sm border border-border rounded bg-surface text-text-primary"
        >
          {governments.map((g) => (
            <option key={g} value={g}>{g || 'All countries'}</option>
          ))}
        </select>
        <input
          placeholder="Filter by topic…"
          value={topicFilter}
          onChange={(e) => setTopicFilter(e.target.value)}
          className="px-2 py-1 text-sm border border-border rounded bg-surface text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-accent"
        />
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-surface-muted">
              <th className="text-left p-2 font-medium text-text-secondary border-b border-border">Topic</th>
              {models.map((m) => (
                <th key={m} className={`p-2 font-medium border-b border-border w-24 text-center ${MODEL_HDR_CLS[m] ?? 'text-text-secondary'}`}>
                  {MODEL_SHORT[m] ?? m}
                </th>
              ))}
              <th className="p-2 font-medium text-text-muted border-b border-border w-16 text-center text-xs">Δ range</th>
            </tr>
          </thead>
          <tbody>
            {groups.map(([government, rows]) => (
              <Fragment key={government}>
                <tr className="bg-accent-subtle">
                  <td colSpan={models.length + 2} className="p-2 font-semibold text-accent text-xs uppercase tracking-wider">
                    {government}
                  </td>
                </tr>
                {rows.map((topic) => {
                  const scores = models.map((m) => lookup[topic.topic_id]?.[m]?.[lang] ?? null)
                  const validScores = scores.filter((s): s is number => s !== null)
                  const max = validScores.length ? Math.max(...validScores) : null
                  const min = validScores.length ? Math.min(...validScores) : null
                  const delta = max !== null && min !== null ? max - min : null
                  const rowMax = max ?? 0

                  return (
                    <Fragment key={topic.topic_id}>
                      <tr
                        onClick={() => setSelectedTopicId(selectedTopicId === topic.topic_id ? null : topic.topic_id)}
                        className={`border-b border-border cursor-pointer transition-colors ${
                          selectedTopicId === topic.topic_id ? 'bg-accent-subtle' : 'hover:bg-surface-muted'
                        }`}
                      >
                        <td className="p-2 text-text-primary">{topic.label}</td>
                        {models.map((m, i) => {
                          const s = scores[i] ?? null
                          const isMax = s !== null && s === rowMax && rowMax > 0
                          return (
                            <td key={m} className="p-2 text-center w-24">
                              {scoreCell(s, isMax)}
                            </td>
                          )
                        })}
                        <td className="p-2 text-center text-xs font-mono text-text-muted">
                          {delta !== null ? delta.toFixed(2) : '—'}
                        </td>
                      </tr>
                      {selectedTopicId === topic.topic_id && (
                        <tr>
                          <td colSpan={models.length + 2} className="p-0">
                            <div className="border-b border-border bg-surface p-4">
                              <div className="flex gap-3 mb-2 text-xs text-text-muted">
                                <span>Showing response viewer for:</span>
                                {models.map((m) => (
                                  <span key={m} className={`font-medium ${MODEL_HDR_CLS[m] ?? ''}`}>{MODEL_SHORT[m] ?? m}</span>
                                ))}
                              </div>
                              {models.map((m) => (
                                <div key={m} className="mb-4 last:mb-0">
                                  <p className={`text-xs font-semibold mb-1 ${MODEL_HDR_CLS[m] ?? 'text-text-secondary'}`}>
                                    {m}
                                  </p>
                                  <BiasResponseViewer topicId={topic.topic_id} model={m} />
                                </div>
                              ))}
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  )
                })}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-3 space-y-1">
        <p className="text-xs text-text-muted">
          Cosine distance from English response (EN = 0.00 baseline). Higher = more divergent.
          Ring marks highest score per row. Δ range = max − min across models.
        </p>
        {models.length < 3 && (
          <p className="text-xs text-text-muted">
            {3 - models.length} model{3 - models.length !== 1 ? 's' : ''} not yet scored — run{' '}
            <code className="font-mono bg-surface-muted px-1 rounded text-xs">attack --mode bias ... && score-bias --model &lt;name&gt;</code>.
          </p>
        )}
      </div>
    </div>
  )
}
