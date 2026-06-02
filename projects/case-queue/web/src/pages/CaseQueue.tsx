import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useCases } from '@/api/cases'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Pagination } from '@/components/Pagination'
import { SeverityBadge } from '@/components/SeverityBadge'
import { StatusBadge } from '@/components/StatusBadge'
import { Card, CardContent } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { CaseCategory, CaseFilters, CaseSortBy, CaseStatus, Severity, SortDir } from '@/types'

const PAGE_SIZE = 50

type SortState = { by: CaseSortBy; dir: SortDir } | null
type Column = { label: string; sortKey?: CaseSortBy }

const COLUMNS: Column[] = [
  { label: 'Case ID' },
  { label: 'Category', sortKey: 'category' },
  { label: 'Severity', sortKey: 'severity' },
  { label: 'Status', sortKey: 'status' },
  { label: 'Created', sortKey: 'created_at' },
]

function SortIcon({ state, col }: { state: SortState; col: CaseSortBy }) {
  if (state?.by !== col) return <span className="ml-1 text-xs text-muted-foreground/40">↕</span>
  return <span className="ml-1 text-xs text-primary">{state.dir === 'asc' ? '▲' : '▼'}</span>
}

const selectCls =
  'rounded-md border border-input bg-background px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring'

export function CaseQueue() {
  const [page, setPage] = useState(1)
  const [category, setCategory] = useState<CaseCategory | ''>('')
  const [severity, setSeverity] = useState<Severity | ''>('')
  const [status, setStatus] = useState<CaseStatus | ''>('')
  const [sort, setSort] = useState<SortState>(null)

  const filters: CaseFilters = {
    page,
    page_size: PAGE_SIZE,
    ...(category && { category }),
    ...(severity && { severity }),
    ...(status && { status }),
    ...(sort && { sort_by: sort.by, sort_dir: sort.dir }),
  }

  const { data, isLoading, isError, error } = useCases(filters)

  function handleFilterChange(setter: (v: string) => void) {
    return (e: React.ChangeEvent<HTMLSelectElement>) => {
      setter(e.target.value)
      setPage(1)
    }
  }

  function handleSort(key: CaseSortBy) {
    setSort((prev) => {
      if (prev?.by !== key) return { by: key, dir: 'asc' }
      if (prev.dir === 'asc') return { by: key, dir: 'desc' }
      return null
    })
    setPage(1)
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-foreground">Case Queue</h1>
        <Link to="/audit" className="text-sm text-primary hover:underline">
          Audit Log →
        </Link>
      </div>

      <div className="mb-4 flex flex-wrap gap-3">
        <select
          value={category}
          onChange={handleFilterChange(setCategory as (v: string) => void)}
          className={selectCls}
        >
          <option value="">All categories</option>
          <option value="toxic">Toxic</option>
          <option value="severe_toxic">Severe Toxic</option>
          <option value="obscene">Obscene</option>
          <option value="threat">Threat</option>
          <option value="insult">Insult</option>
          <option value="identity_hate">Identity Hate</option>
        </select>

        <select
          value={severity}
          onChange={handleFilterChange(setSeverity as (v: string) => void)}
          className={selectCls}
        >
          <option value="">All severities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>

        <select
          value={status}
          onChange={handleFilterChange(setStatus as (v: string) => void)}
          className={selectCls}
        >
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="escalated">Escalated</option>
        </select>
      </div>

      {isError && (
        <div className="mb-4">
          <ErrorMessage message={(error as Error).message ?? 'Failed to load cases'} />
        </div>
      )}

      {isLoading && (
        <div className="py-12 text-center text-sm text-muted-foreground">Loading cases…</div>
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
                        No cases match the current filters.
                      </TableCell>
                    </TableRow>
                  ) : (
                    data.items.map((c) => (
                      <TableRow key={c.id}>
                        <TableCell>
                          <Link
                            to={`/cases/${c.id}`}
                            className="font-mono text-sm text-primary hover:underline"
                          >
                            {c.id.slice(0, 8)}
                          </Link>
                        </TableCell>
                        <TableCell className="text-sm text-foreground">
                          {c.category.replace('_', ' ')}
                        </TableCell>
                        <TableCell>
                          <SeverityBadge severity={c.severity} />
                        </TableCell>
                        <TableCell>
                          <StatusBadge status={c.status} />
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {new Date(c.created_at).toLocaleDateString()}
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
