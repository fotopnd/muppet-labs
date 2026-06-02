import { Badge } from '@/components/ui/badge'
import type { Severity } from '@/types'

const STYLES: Record<Severity, string> = {
  low: 'bg-gray-100 text-gray-700 border-transparent hover:bg-gray-100',
  medium: 'bg-orange-100 text-orange-800 border-transparent hover:bg-orange-100',
  high: 'bg-red-100 text-red-800 border-transparent hover:bg-red-100',
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  return <Badge className={STYLES[severity]}>{severity}</Badge>
}
