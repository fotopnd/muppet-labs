import { createPortal } from 'react-dom'

type Props = {
  floaterPos: { top: number; left: number } | null
  pendingExcerpt: string | null
  onFlag: (excerpt: string) => void
}

export function SelectionFloater({ floaterPos, pendingExcerpt, onFlag }: Props) {
  if (!floaterPos || !pendingExcerpt) return null

  return createPortal(
    <button
      data-floater
      style={{ position: 'fixed', top: floaterPos.top, left: floaterPos.left }}
      className="bg-accent text-white font-interface text-sm px-3 py-1.5 rounded shadow-lg z-50 hover:bg-blue-700 transition-colors cursor-pointer"
      onMouseDown={(e) => e.preventDefault()}
      onClick={() => onFlag(pendingExcerpt)}
    >
      Flag selection
    </button>,
    document.body,
  )
}
