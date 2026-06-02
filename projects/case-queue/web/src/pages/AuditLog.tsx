import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuditActors, useAuditLog } from '@/api/audit'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Pagination } from '@/components/Pagination'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { Action, AuditFilters, AuditSortBy, SortDir } from '@/types'

const PAGE_SIZE = 50

type SortState = { by: AuditSortBy; dir: SortDir } | null
type Column = { label: string; sortKey?: AuditSortBy }

const COLUMNS: Column[] = [
  { label: 'Timestamp', sortKey: 'created_at' },
  { label: 'Case ID' },
  { label: 'Actor', sortKey: 'actor_id' },
  { label: 'Action', sortKey: 'action' },
  { label: 'Notes' },
]

const ACTION_STYLES: Record<Action, string> = {
  approve: 'bg-green-100 text-green-800 border-transparent hover:bg-green-100',
  reject: 'bg-red-100 text-red-800 border-transparent hover:bg-red-100',
  escalate: 'bg-purple-100 text-purple-800 border-transparent hover:bg-purple-100',
}

function SortIcon({ state, col }: { state: SortState; col: AuditSortBy }) {
  if (state?.by !== col) return <span className="ml-1 text-xs text-muted-foreground/40">↕</span>
  return <span className="ml-1 text-xs text-primary">{state.dir === 'asc' ? '▲' : '▼'}</span>
}

const selectCls =
  'rounded-md border border-input bg-background px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring'

export function AuditLog() {
  const [page, setPage] = useState(1)
  const [action, setAction] = useState<Action | ''>('')
  const [actorId, setActorId] = useState('')
  const [sort, setSort] = useState<SortState>(null)

  const { data: actors } = useAuditActors()

  const filters: AuditFilters = {
    page,
    page_size: PAGE_SIZE,
    ...(action && { action }),
    ...(actorId && { actor_id: actorId }),
    ...(sort && { sort_by: sort.by, sort_dir: sort.dir }),
  }

  const { data, isLoading, isError, error } = useAuditLog(filters)

  function handleSort(key: AuditSortBy) {
    setSort((prev) => {
      if (prev?.by !== key) return { by: key, dir: 'asc' }
      if (prev.dir === 'asc') return { by: key, dir: 'desc' }
      return null
    })
    setPage(1)
  }

  const aiActors = actors?.filter((a) => a.startsWith('ai-')) ?? []
  const isAiOnly = aiActors.length > 0 && aiActors.includes(actorId)

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-foreground">Audit Log</h1>
        <Link to="/" className="text-sm text-primary hover:underline">
          ← Case Queue
        </Link>
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <select
          value={action}
          onChange={(e) => {
            setAction(e.target.value as Action | '')
            setPage(1)
          }}
          className={selectCls}
        >
          <option value="">All decisions</option>
          <option value="approve">Approve</option>
          <option value="reject">Reject</option>
          <option value="escalate">Escalate</option>
        </select>

        <select
          value={actorId}
          onChange={(e) => {
            setActorId(e.target.value)
            setPage(1)
          }}
          className={selectCls}
        >
          <option value="">All actors</option>
          {actors?.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>

        {aiActors.length > 0 && (
          <Button
            variant={isAiOnly ? 'secondary' : 'outline'}
            size="sm"
            onClick={() => {
              setActorId(isAiOnly ? '' : 'ai-reviewer')
              setPage(1)
            }}
          >
            AI Reviewer only
          </Button>
        )}
      </div>

      {isError && (
        <div className="mb-4">
          <ErrorMessage message={(error as Error).message ?? 'Failed to load audit log'} />
        </div>
      )}

      {isLoading && (
        <div className="py-12 text-center text-sm text-muted-foreground">Loading…</div>
      )}

      {data && (
        <>
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    {COLUMNS.map((col) => (
                      <TableHead
                        key={col.label}
                        onClick={col.sortKey ? () => handleSort(col.sortKey!) : undefined}
                        className={
                          col.sortKey
                            ? 'cursor-pointer select-none text-xs font-medium uppercase tracking-wider hover:text-foreground'
                            : 'text-xs font-medium uppercase tracking-wider'
                        }
                      >
                        {col.label}
                        {col.sortKey && <SortIcon state={sort} col={col.sortKey} />}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.items.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
                        No decisions recorded yet.
                      </TableCell>
                    </TableRow>
                  ) : (
                    data.items.map((entry) => (
                      <TableRow key={entry.id}>
                        <TableCell className="text-sm text-muted-foreground">
                          {new Date(entry.created_at).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          <Link
                            to={`/cases/${entry.case_id}`}
                            className="font-mono text-sm text-primary hover:underline"
                          >
                            {entry.case_id.slice(0, 8)}
                          </Link>
                        </TableCell>
                        <TableCell className="text-sm text-foreground">{entry.actor_id}</TableCell>
                        <TableCell>
                          <Badge className={ACTION_STYLES[entry.action]}>{entry.action}</Badge>
                        </TableCell>
                        <TableCell className="max-w-xs text-sm text-muted-foreground">
                          <span title={entry.notes}>
                            {entry.notes.length > 80
                              ? entry.notes.slice(0, 80) + '…'
                              : entry.notes}
                          </span>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  )
}
