import type { SourceDataset } from '@/types'

const COLORS: Record<SourceDataset, string> = {
  'hh-rlhf': 'bg-blue-100 text-blue-800',
  wildguard: 'bg-purple-100 text-purple-800',
  advbench: 'bg-red-100 text-red-800',
  jailbreakbench: 'bg-orange-100 text-orange-800',
  live: 'bg-green-100 text-green-800',
}

const LABELS: Record<SourceDataset, string> = {
  'hh-rlhf': 'HH-RLHF',
  wildguard: 'WildGuard',
  advbench: 'AdvBench',
  jailbreakbench: 'JailbreakBench',
  live: 'Live',
}

export function SourceBadge({ source }: { source: SourceDataset }) {
  const cls = COLORS[source] ?? 'bg-gray-100 text-gray-800'
  const label = LABELS[source] ?? source
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cls}`} data-testid="source-badge">
      {label}
    </span>
  )
}
