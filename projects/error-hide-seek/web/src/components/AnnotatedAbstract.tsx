import type { Annotation } from '@/types'

type Segment =
  | { kind: 'plain'; text: string }
  | { kind: 'highlight'; text: string; annotation: Annotation }

function buildSegments(abstract: string, annotations: Annotation[]): Segment[] {
  const lower = abstract.toLowerCase()

  const found = annotations
    .map((ann) => ({ ann, idx: lower.indexOf(ann.text_excerpt.toLowerCase()) }))
    .filter((x) => x.idx !== -1)
    .sort((a, b) => a.idx - b.idx)

  const segments: Segment[] = []
  let pos = 0
  let coveredUntil = 0

  for (const { ann, idx } of found) {
    if (idx < coveredUntil) continue
    if (idx > pos) segments.push({ kind: 'plain', text: abstract.slice(pos, idx) })
    const end = idx + ann.text_excerpt.length
    segments.push({ kind: 'highlight', text: abstract.slice(idx, end), annotation: ann })
    pos = end
    coveredUntil = end
  }

  if (pos < abstract.length) segments.push({ kind: 'plain', text: abstract.slice(pos) })
  return segments
}

const HIGHLIGHT_CLASS: Record<Annotation['confidence'], string> = {
  high: 'bg-amber-200 text-amber-900 cursor-help rounded px-0.5',
  medium: 'bg-yellow-100 text-yellow-800 cursor-help rounded px-0.5',
  low: 'bg-slate-100 text-slate-600 cursor-help rounded px-0.5',
}

const BADGE_CLASS: Record<Annotation['confidence'], string> = {
  high: 'inline-block bg-amber-500 text-white text-xs px-1 rounded',
  medium: 'inline-block bg-yellow-400 text-yellow-900 text-xs px-1 rounded',
  low: 'inline-block bg-slate-400 text-white text-xs px-1 rounded',
}

type Props = {
  abstract: string
  annotations: Annotation[]
}

export function AnnotatedAbstract({ abstract, annotations }: Props) {
  const segments = buildSegments(abstract, annotations)

  return (
    <div className="font-data text-sm leading-relaxed text-text-default whitespace-pre-wrap bg-surface rounded-lg border border-border p-6">
      {segments.map((seg, i) => {
        if (seg.kind === 'plain') {
          return <span key={i}>{seg.text}</span>
        }
        const { annotation } = seg
        return (
          <span key={i} className="relative group inline">
            <span className={HIGHLIGHT_CLASS[annotation.confidence]}>{seg.text}</span>
            <span className="absolute bottom-full left-0 z-10 mb-1 hidden group-hover:block bg-slate-800 text-slate-50 text-xs rounded px-2 py-1.5 max-w-xs whitespace-normal shadow-lg pointer-events-none">
              <span className={BADGE_CLASS[annotation.confidence]}>{annotation.confidence}</span>{' '}
              {annotation.reason}
            </span>
          </span>
        )
      })}
    </div>
  )
}
