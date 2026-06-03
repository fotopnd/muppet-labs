import { ExternalLink } from 'lucide-react'
import type { CaseListItem } from '@/types'

type EscalationCaseRowProps = {
  caseItem: CaseListItem
  caseQueueUrl: string
}

export function EscalationCaseRow({ caseItem, caseQueueUrl }: EscalationCaseRowProps) {
  return (
    <a
      href={`${caseQueueUrl}/cases/${caseItem.id}`}
      target="_blank"
      rel="noopener noreferrer"
      className="group"
    >
      <li className="flex items-center gap-4 py-3 border-b border-border last:border-0 hover:bg-accent-subtle/50">
        <span className="font-interface text-sm text-text-default truncate flex-1 min-w-0">
          {caseItem.content}
        </span>
        <span className="font-data text-xs px-2 py-0.5 rounded bg-accent-subtle text-accent flex-shrink-0">
          {caseItem.category}
        </span>
        <span
          className={[
            'font-data text-xs px-2 py-0.5 rounded flex-shrink-0',
            caseItem.source === 'moderation-dashboard'
              ? 'bg-danger/10 text-danger'
              : 'bg-warning/10 text-warning',
          ].join(' ')}
        >
          {caseItem.source}
        </span>
        <ExternalLink
          size={14}
          className="text-text-muted group-hover:text-accent flex-shrink-0"
        />
      </li>
    </a>
  )
}
