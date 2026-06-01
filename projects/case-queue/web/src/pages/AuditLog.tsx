import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuditActors, useAuditLog } from '@/api/audit'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Pagination } from '@/components/Pagination'
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

function SortIcon({ state, col }: { state: SortState; col: AuditSortBy }) {
  if (state?.by !== col) return <span className="ml-1 text-xs text-gray-300">↕</span>
  return (
    <span className="ml-1 text-xs text-blue-600">{state.dir === 'asc' ? '▲' : '▼'}</span>
  )
}

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
        <h1 className="text-2xl font-semibold text-gray-900">Audit Log</h1>
        <Link to="/" className="text-sm text-blue-600 hover:underline">
          ← Case Queue
        </Link>
      </div>

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <select
          value={action}
          onChange={(e) => {
            setAction(e.target.value as Action | '')
            setPage(1)
          }}
          className="rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
          className="rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All actors</option>
          {actors?.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>

        {aiActors.length > 0 && (
          <button
            onClick={() => {
              setActorId((prev) => (isAiOnly ? '' : 'ai-reviewer'))
              setPage(1)
            }}
            className={`rounded border px-3 py-1.5 text-sm ${
              isAiOnly
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            AI Reviewer only
          </button>
        )}
      </div>

      {isError && (
        <ErrorMessage message={(error as Error).message ?? 'Failed to load audit log'} />
      )}

      {isLoading && (
        <div className="py-12 text-center text-sm text-gray-500">Loading…</div>
      )}

      {data && (
        <>
          <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {COLUMNS.map((col) => (
                    <th
                      key={col.label}
                      onClick={col.sortKey ? () => handleSort(col.sortKey!) : undefined}
                      className={`px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 ${
                        col.sortKey ? 'cursor-pointer select-none hover:text-gray-700' : ''
                      }`}
                    >
                      {col.label}
                      {col.sortKey && <SortIcon state={sort} col={col.sortKey} />}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {data.items.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-sm text-gray-400">
                      No decisions recorded yet.
                    </td>
                  </tr>
                ) : (
                  data.items.map((entry) => (
                    <tr key={entry.id} className="hover:bg-gray-50">
                      <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                        {new Date(entry.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3">
                        <Link
                          to={`/cases/${entry.case_id}`}
                          className="font-mono text-sm text-blue-600 hover:underline"
                        >
                          {entry.case_id.slice(0, 8)}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">{entry.actor_id}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${
                            entry.action === 'approve'
                              ? 'bg-green-100 text-green-800'
                              : entry.action === 'reject'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-purple-100 text-purple-800'
                          }`}
                        >
                          {entry.action}
                        </span>
                      </td>
                      <td className="max-w-xs px-4 py-3 text-sm text-gray-600">
                        <span title={entry.notes}>
                          {entry.notes.length > 80
                            ? entry.notes.slice(0, 80) + '…'
                            : entry.notes}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

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
