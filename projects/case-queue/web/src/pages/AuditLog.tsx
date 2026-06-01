import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuditLog } from '@/api/audit'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Pagination } from '@/components/Pagination'
import type { AuditFilters } from '@/types'

const PAGE_SIZE = 50

export function AuditLog() {
  const [page, setPage] = useState(1)
  const filters: AuditFilters = { page, page_size: PAGE_SIZE }
  const { data, isLoading, isError, error } = useAuditLog(filters)

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Audit Log</h1>
        <Link to="/" className="text-sm text-blue-600 hover:underline">
          ← Case Queue
        </Link>
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
                  {['Timestamp', 'Case ID', 'Actor', 'Action', 'Notes'].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                    >
                      {h}
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
