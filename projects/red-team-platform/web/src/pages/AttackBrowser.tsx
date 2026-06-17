import { useState } from 'react'
import { useAttacks } from '@/hooks/useAttacks'
import { useHarmCategories, useStrategies } from '@/hooks/useAttackFilters'
import { useAttackSummary } from '@/hooks/useAttackSummary'
import { StatWidget } from '@/components/StatWidget'
import { ScoreBar } from '@/components/ScoreBar'
import { labelName } from '@/lib/categoryLabels'
import { STRATEGY_DESCRIPTIONS } from '@/lib/strategyDescriptions'
import type { Attack } from '@/types'

export function AttackBrowser() {
  const [page, setPage] = useState(1)
  const pageSize = 20
  const [source, setSource] = useState('')
  const [harmCategory, setHarmCategory] = useState('')
  const [strategy, setStrategy] = useState('')
  const [selectedAttack, setSelectedAttack] = useState<Attack | null>(null)

  const { data, isLoading, isError } = useAttacks({ page, pageSize, source, harmCategory, strategy })
  const { data: cats } = useHarmCategories()
  const { data: strats } = useStrategies()
  const { data: summary, isLoading: summaryLoading } = useAttackSummary({
    source: source || null,
    harm_category: harmCategory || null,
    strategy: strategy || null,
  })

  const stratMeta = selectedAttack ? STRATEGY_DESCRIPTIONS[selectedAttack.strategy] : null

  return (
    <div className="p-4">
      <div className="grid grid-cols-3 gap-4 mb-5">
        <StatWidget
          label="Total attacks"
          value={summaryLoading ? '…' : (summary?.total ?? 0)}
          loading={summaryLoading}
        />
        <StatWidget
          label="Top category"
          value={summaryLoading ? '…' : (summary?.top_category ? labelName(summary!.top_category).split('/')[0]!.trim() : '—')}
          {...(summary?.top_category ? { subLabel: labelName(summary.top_category) } : {})}
          loading={summaryLoading}
        />
        <StatWidget
          label="Top strategy"
          value={summaryLoading ? '…' : (summary?.top_strategy ? STRATEGY_DESCRIPTIONS[summary.top_strategy]?.label ?? summary.top_strategy : '—')}
          loading={summaryLoading}
        />
      </div>

      <div className="flex gap-2 mb-4 flex-wrap">
        <input
          placeholder="Source filter"
          value={source}
          onChange={(e) => { setSource(e.target.value); setPage(1) }}
          className="px-2 py-1 text-sm border border-border rounded bg-surface text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-accent"
        />
        <select
          value={harmCategory}
          onChange={(e) => { setHarmCategory(e.target.value); setPage(1) }}
          className="px-2 py-1 text-sm border border-border rounded bg-surface text-text-primary focus:outline-none focus:ring-1 focus:ring-accent"
        >
          <option value="">All categories</option>
          {cats?.values.map((c) => <option key={c} value={c}>{labelName(c)}</option>)}
        </select>
        <select
          value={strategy}
          onChange={(e) => { setStrategy(e.target.value); setPage(1) }}
          className="px-2 py-1 text-sm border border-border rounded bg-surface text-text-primary focus:outline-none focus:ring-1 focus:ring-accent"
        >
          <option value="">All strategies</option>
          {strats?.values.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      <div className="flex gap-4">
        <div className={selectedAttack ? 'flex-1 min-w-0' : 'w-full'}>
          {isLoading && <p className="text-text-secondary text-sm">Loading…</p>}
          {isError && <p className="text-danger text-sm">Error loading attacks.</p>}
          {data && (
            <>
              <p className="text-xs text-text-muted mb-2">{data.total} total</p>
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-surface-muted">
                    <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">Source</th>
                    <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">Category</th>
                    <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">Strategy</th>
                    <th className="text-left px-3 py-2 font-medium text-text-secondary border-b border-border">Attack Text</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((atk) => (
                    <tr
                      key={atk.id}
                      onClick={() => setSelectedAttack(selectedAttack?.id === atk.id ? null : atk)}
                      className={`border-b border-border cursor-pointer transition-colors ${
                        selectedAttack?.id === atk.id ? 'bg-accent-subtle' : 'hover:bg-surface-muted'
                      }`}
                    >
                      <td className="px-3 py-2 align-top text-text-secondary">{atk.source}</td>
                      <td className="px-3 py-2 align-top text-text-primary">{labelName(atk.harm_category)}</td>
                      <td className="px-3 py-2 align-top text-text-primary font-mono text-xs">{atk.strategy}</td>
                      <td className="px-3 py-2 align-top text-text-primary">
                        {atk.attack_text.slice(0, 120)}{atk.attack_text.length > 120 ? '…' : ''}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="flex gap-2 mt-3 items-center">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 text-sm border border-border rounded bg-surface text-text-primary disabled:opacity-40 hover:bg-surface-muted"
                >
                  Prev
                </button>
                <span className="text-sm text-text-secondary">Page {page}</span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page * pageSize >= data.total}
                  className="px-3 py-1 text-sm border border-border rounded bg-surface text-text-primary disabled:opacity-40 hover:bg-surface-muted"
                >
                  Next
                </button>
              </div>
            </>
          )}
        </div>

        {selectedAttack && (
          <div className="w-[40%] min-w-72 border border-border rounded-lg bg-surface p-4 self-start sticky top-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-3">
              <p className="text-sm font-semibold text-text-primary">Attack Detail</p>
              <button
                onClick={() => setSelectedAttack(null)}
                className="text-text-muted hover:text-text-primary text-lg leading-none"
              >
                ×
              </button>
            </div>

            <div className="mb-4">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
                  Attack Text
                </span>
                <span className="text-xs text-text-muted font-mono">
                  {selectedAttack.attack_text.length} chars
                </span>
              </div>
              <pre className="bg-surface-muted rounded p-2 text-xs font-mono whitespace-pre-wrap break-words text-text-primary max-h-64 overflow-y-auto">
                {selectedAttack.attack_text}
              </pre>
            </div>

            <dl className="border border-border rounded p-3 bg-canvas text-xs space-y-3 mb-4">
              <div>
                <dt className="font-semibold text-text-secondary mb-0.5">Strategy</dt>
                <dd className="text-text-primary font-medium">
                  {stratMeta?.label ?? selectedAttack.strategy}
                </dd>
                {stratMeta && (
                  <>
                    <dd className="text-text-secondary mt-1 leading-relaxed">{stratMeta.description}</dd>
                    <dd className="mt-2">
                      <span className="text-text-muted text-xs uppercase tracking-wider font-semibold">Example template</span>
                      <code className="block bg-surface-muted rounded p-2 text-xs font-mono whitespace-pre-wrap mt-1 text-text-primary">
                        {stratMeta.example}
                      </code>
                    </dd>
                  </>
                )}
              </div>
              <div>
                <dt className="font-semibold text-text-secondary mb-0.5">Category</dt>
                <dd className="text-text-primary font-medium">{labelName(selectedAttack.harm_category)}</dd>
              </div>
            </dl>

            <div className="text-xs text-text-muted">
              <span className="font-mono">{selectedAttack.source}</span> · {selectedAttack.created_at.slice(0, 10)}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
