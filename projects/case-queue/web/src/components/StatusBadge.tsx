import type { CaseStatus } from '@/types'

const STYLES: Record<CaseStatus, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  escalated: 'bg-purple-100 text-purple-800',
}

export function StatusBadge({ status }: { status: CaseStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STYLES[status]}`}
    >
      {status}
    </span>
  )
}
