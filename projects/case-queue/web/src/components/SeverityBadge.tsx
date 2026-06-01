import type { Severity } from '@/types'

const STYLES: Record<Severity, string> = {
  low: 'bg-gray-100 text-gray-700',
  medium: 'bg-orange-100 text-orange-800',
  high: 'bg-red-100 text-red-800',
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STYLES[severity]}`}
    >
      {severity}
    </span>
  )
}
