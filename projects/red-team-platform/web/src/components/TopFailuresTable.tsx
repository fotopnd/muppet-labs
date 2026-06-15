import { useState } from 'react'
import { useTopFailures } from '@/hooks/useTopFailures'
import { labelName } from '@/lib/categoryLabels'
import type { TopFailure } from '@/types'

const ATTACK_MAX  = 500
const RESPONSE_MAX = 180

function clip(text: string, max: number): { text: string; clipped: boolean } {
  if (text.length <= max) return { text, clipped: false }
  return { text: text.slice(0, max).trimEnd(), clipped: true }
}

const MODEL_CLS: Record<string, string> = {
  'gemma2:9b':    'text-blue-700',
  'qwen2.5:7b':  'text-orange-700',
  'llama3.1:8b': 'text-violet-700',
}

function FailureRow({ f, expanded, onToggle }: {
  f: TopFailure
  expanded: boolean
  onToggle: () => void
}) {
  return (
    <>
      <tr
        onClick={onToggle}
        className={`border-b border-border cursor-pointer transition-colors ${expanded ? 'bg-accent-subtle' : 'hover:bg-surface-muted'}`}
      >
        <td className="px-3 py-2 font-mono text-xs text-text-primary whitespace-nowrap">{f.strategy}</td>
        <td className="px-3 py-2 text-xs text-text-secondary">{labelName(f.harm_category)}</td>
        <td className={`px-3 py-2 text-xs font-medium whitespace-nowrap ${MODEL_CLS[f.model_name] ?? 'text-text-secondary'}`}>
          {f.model_name}
        </td>
        <td className="px-3 py-2 text-right">
          <span className="inline-block font-mono text-xs font-semibold bg-red-50 text-red-700 px-1.5 py-0.5 rounded">
            {f.classifier_score.toFixed(2)}
          </span>
        </td>
        <td className="px-3 py-2 text-xs text-text-muted max-w-xs truncate">{f.attack_text}</td>
        <td className="px-3 py-2 text-center text-text-muted text-xs">{expanded ? '▲' : '▼'}</td>
      </tr>
      {expanded && (
        <tr className="border-b border-border bg-surface">
          <td colSpan={6} className="px-4 py-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div>
                <p className="font-semibold text-text-secondary uppercase tracking-wider text-xs mb-1.5">Attack Prompt</p>
                <p className="text-text-primary leading-relaxed whitespace-pre-wrap font-mono bg-surface-muted rounded p-2 max-h-48 overflow-y-auto">
                  {clip(f.attack_text, ATTACK_MAX).text}
                  {clip(f.attack_text, ATTACK_MAX).clipped && (
                    <span className="text-text-muted not-italic"> …[truncated]</span>
                  )}
                </p>
              </div>
              <div>
                <p className="font-semibold text-text-secondary uppercase tracking-wider text-xs mb-1.5">Model Response</p>
                <p className="text-text-primary leading-relaxed whitespace-pre-wrap bg-danger/5 border border-danger/20 rounded p-2">
                  {clip(f.response_text, RESPONSE_MAX).text}
                  <span className="text-text-muted"> …[truncated for content safety]</span>
                </p>
                <p className="text-xs text-text-muted mt-1">
                  Sourced from the WildGuard academic red-team corpus. Response truncated.
                </p>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

export function TopFailuresTable() {
  const { data, isLoading, isError } = useTopFailures(20)
  const [expandedId, setExpandedId] = useState<string | null>(null)

  if (isLoading) return <p className="text-text-secondary text-sm">Loading…</p>
  if (isError) return <p className="text-danger text-sm">Error loading failures.</p>
  if (!data?.items.length) return <p className="text-text-muted text-sm">No successful jailbreaks found.</p>

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-surface-muted border-b border-border">
              <th className="text-left px-3 py-2 font-medium text-text-secondary text-xs">Strategy</th>
              <th className="text-left px-3 py-2 font-medium text-text-secondary text-xs">Harm Category</th>
              <th className="text-left px-3 py-2 font-medium text-text-secondary text-xs">Model</th>
              <th className="text-right px-3 py-2 font-medium text-text-secondary text-xs">Score</th>
              <th className="text-left px-3 py-2 font-medium text-text-secondary text-xs">Prompt (truncated)</th>
              <th className="w-8" />
            </tr>
          </thead>
          <tbody>
            {data.items.map((f) => (
              <FailureRow
                key={f.run_id}
                f={f}
                expanded={expandedId === f.run_id}
                onToggle={() => setExpandedId(expandedId === f.run_id ? null : f.run_id)}
              />
            ))}
          </tbody>
        </table>
      </div>
      <p className="px-3 py-2 text-xs text-text-muted border-t border-border">
        Top 20 highest-confidence jailbreak successes (classifier score ≥ 0.99). Prompts and responses sourced from the WildGuard academic red-team corpus and truncated for content safety. Click any row to expand.
      </p>
    </div>
  )
}
