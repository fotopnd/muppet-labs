# Frontend-Architect Output — red-team-platform v5

**Role:** frontend-architect
**Sequence:** add-feature
**Date:** 2026-06-15

## Component Tree

```
App.tsx
├── StrategyExplorer (existing)
├── Analytics (existing + LiveFeed section added)
│   └── LiveFeed (new inline component within Analytics.tsx)
├── BiasHeatmap (existing)
├── Glossary (existing)
├── CaseReview (new page)
│   ├── TriageSummaryBadges (inline component)
│   ├── TriageFilterToggle (inline component)
│   ├── RunTable (inline, handles Compare + All modes)
│   └── DecisionForm (inline component, shared across Compare + All modes)
└── AuditLog (new page)
    └── AuditTable (inline component)
```

## Hook Signatures

### useCaseReview.ts
```typescript
// Query: get decision for a run (null if 404)
export function useCaseReview(runId: string | null) {
  return useQuery({
    queryKey: ['case-review', runId],
    queryFn: async () => { /* GET /runs/{runId}/review; return null on 404 */ },
    enabled: !!runId,
    staleTime: 5_000,
  })
}

// Mutation: submit decision
export function useSubmitReview() {
  return useMutation({
    mutationFn: (payload: { runId: string; decision: string; reason: string | null }) =>
      fetch(`/runs/${payload.runId}/review`, { method: 'POST', ... }),
    onSuccess: (_, { runId }) => queryClient.invalidateQueries({ queryKey: ['case-review', runId] }),
  })
}
```

### useAuditLog.ts
```typescript
export function useAuditLog(params: { decision?: string; reviewer?: string; limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ['audit-log', params],
    queryFn: () => fetch(`/audit-log?${buildParams(params)}`).then(r => r.json()),
    staleTime: 5_000,
  })
}
```

### useTriageSummary.ts
```typescript
export function useTriageSummary() {
  return useQuery({
    queryKey: ['triage-summary'],
    queryFn: () => fetch('/runs/triage-summary').then(r => r.json()),
    staleTime: 30_000,
  })
}
```

## State Management — CaseReview

```typescript
const [mode, setMode] = useState<'compare' | 'all'>('compare')
const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
const [triageTier, setTriageTier] = useState<string | undefined>('review')  // default = Needs Review
const [page, setPage] = useState(1)
const [selectedGroup, setSelectedGroup] = useState<GroupedRow | null>(null)
const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
const [editingRunId, setEditingRunId] = useState<string | null>(null)  // which run has form open
```

## State Management — AuditLog

```typescript
const [decisionFilter, setDecisionFilter] = useState<string>('')
const [reviewerFilter, setReviewerFilter] = useState<string>('')
const [offset, setOffset] = useState(0)
const limit = 50
```

## State Management — LiveFeed

```typescript
const [isOpen, setIsOpen] = useState(false)
const [events, setEvents] = useState<RunEvent[]>([])
const [running, setRunning] = useState(false)
const [speed, setSpeed] = useState<'fast' | 'normal' | 'slow'>('normal')
const [count, setCount] = useState(0)
const esRef = useRef<EventSource | null>(null)
```

## API Base URL

Check existing hooks for base URL pattern. Looking at existing hooks — they likely use a relative `/` path or an env var. The decision form posts to `/runs/${runId}/review` using the same base URL pattern.

## New TypeScript Types (index.ts additions)

```typescript
export type TriageTier = 'auto_safe' | 'review' | 'auto_flag'

// Extend Run with triage_tier
// Run type gets: triage_tier: TriageTier

export type CaseReview = {
  id: string
  run_id: string
  decision: 'approve' | 'flag' | 'escalate'
  reason: string | null
  reviewed_at: string
  reviewer: string
}

export type AuditLogEntry = {
  id: string
  run_id: string
  action: string
  decision: string
  reason: string | null
  reviewer: string
  created_at: string
}

export type AuditLogOut = {
  items: AuditLogEntry[]
  total: number
  limit: number
  offset: number
}

export type TriageSummaryOut = {
  auto_safe: number
  review: number
  auto_flag: number
}

export type RunEvent = {
  id: string
  strategy: string
  model_name: string
  harm_category: string
  classifier_score: number
  jailbreak_success: boolean
  created_at: string
}
```

## Implementation Notes

1. **API base URL**: Check `/Users/fotopnd/Documents/muppet-labs/projects/red-team-platform/web/src/hooks/` for an existing base URL constant. Use the same pattern.

2. **DecisionForm isolation**: Each run has its own independent query (`useCaseReview(runId)`). The form shows only when `selectedRunId` or `selectedGroup` is active. This avoids N+1 fetches — only the selected run's decision is fetched.

3. **CaseReview replaces SampleReview**: `SampleReview.tsx` stays on disk (not deleted — conservative). `App.tsx` imports `CaseReview` instead. The tab label becomes "Case Review".

4. **Live Feed EventSource**: Create with `new EventSource(\`${API_BASE}/runs/stream?speed=${speed}\`)`. On `message` event append to `events` (keep last 50). On `error` or custom `done` event, close and setRunning(false). Pause = `esRef.current?.close(); setRunning(false)`.

5. **Reviewer dropdown in AuditLog**: Since reviewers are currently only "analyst-1" (hardcoded), the dropdown can be static for now. Brief says filter dropdowns — implement as a static select with known values.

## Handoff

Next role: implementer (backend phase)
All backend code to write is fully specified. Proceed to implementation.
