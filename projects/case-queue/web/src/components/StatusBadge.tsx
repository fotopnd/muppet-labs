import { Badge } from '@/components/ui/badge'
import type { CaseStatus } from '@/types'

const STYLES: Record<CaseStatus, string> = {
  pending: 'bg-yellow-100 text-yellow-800 border-transparent hover:bg-yellow-100',
  approved: 'bg-green-100 text-green-800 border-transparent hover:bg-green-100',
  rejected: 'bg-red-100 text-red-800 border-transparent hover:bg-red-100',
  escalated: 'bg-purple-100 text-purple-800 border-transparent hover:bg-purple-100',
}

export function StatusBadge({ status }: { status: CaseStatus }) {
  return <Badge className={STYLES[status]}>{status}</Badge>
}
