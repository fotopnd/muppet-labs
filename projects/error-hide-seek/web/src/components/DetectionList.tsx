import type { DetectionIn } from '@/types'

type Props = {
  detections: DetectionIn[]
  onRemove: (index: number) => void
  onNoteChange: (index: number, note: string) => void
  onSubmit: () => void
  submitting: boolean
}

export function DetectionList({ detections, onRemove, onNoteChange, onSubmit, submitting }: Props) {
  return (
    <div className="flex flex-col gap-4">
      <h3 className="font-interface text-sm font-semibold text-text-intense">Flagged errors</h3>

      {detections.length === 0 ? (
        <p className="font-interface text-sm text-text-muted italic">
          No errors flagged yet — select text above to flag.
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {detections.map((det, i) => (
            <li
              key={i}
              className="flex items-start gap-3 p-3 bg-surface rounded border border-border"
            >
              <div className="flex-1 flex flex-col gap-1 min-w-0">
                <span className="font-data text-xs text-text-intense break-all block">
                  {det.text_excerpt.length > 60
                    ? det.text_excerpt.slice(0, 60) + '…'
                    : det.text_excerpt}
                </span>
                <input
                  type="text"
                  value={det.note ?? ''}
                  onChange={(e) => onNoteChange(i, e.target.value)}
                  placeholder="Add note (optional)"
                  className="w-full font-interface text-xs bg-transparent border-0 border-b border-border pb-0.5 text-text-default placeholder:text-text-muted focus:outline-none focus:border-accent"
                />
              </div>
              <button
                onClick={() => onRemove(i)}
                aria-label="Remove"
                className="text-text-muted hover:text-danger transition-colors shrink-0 font-data text-base"
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="pt-4 border-t border-border flex flex-col gap-2">
        <p className="font-interface text-xs text-text-muted">
          Submitting with no flags means you found nothing suspicious.
        </p>
        <button
          onClick={onSubmit}
          disabled={submitting}
          className="px-4 py-2 bg-accent text-white font-interface text-sm rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2 w-fit"
        >
          {submitting ? (
            <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
          ) : (
            'Submit'
          )}
        </button>
      </div>
    </div>
  )
}
