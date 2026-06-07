import type { Session } from '@/types'

const CONDITION_BADGE: Record<Session['condition'], string> = {
  unaided: 'bg-slate-100 text-slate-600 font-interface text-xs px-2 py-0.5 rounded',
  agent_only: 'bg-accent-subtle text-accent font-interface text-xs px-2 py-0.5 rounded',
  human_agent: 'bg-amber-50 text-amber-700 font-interface text-xs px-2 py-0.5 rounded',
}

const CONDITION_LABEL: Record<Session['condition'], string> = {
  unaided: 'Unaided',
  agent_only: 'Agent Only',
  human_agent: 'Human + Agent',
}

type Props = {
  session: Session
}

export function PaperHeader({ session }: Props) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 flex-wrap">
        <span className={CONDITION_BADGE[session.condition]}>
          {CONDITION_LABEL[session.condition]}
        </span>
        <span className="font-interface text-xs text-text-muted">{session.paper_id}</span>
      </div>
      <h1 className="font-interface text-lg font-semibold text-text-intense leading-snug">
        {session.paper_title}
      </h1>
    </div>
  )
}
