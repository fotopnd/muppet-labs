import type { ModelStatus } from '@/types'

export function StatusBadge({ status }: { status: ModelStatus }) {
  if (status === 'active') {
    return (
      <span className="bg-success/10 text-success text-xs font-data px-2 py-0.5 rounded-full">
        active
      </span>
    )
  }
  return (
    <span className="bg-warning/10 text-warning text-xs font-data px-2 py-0.5 rounded-full">
      pending
    </span>
  )
}
