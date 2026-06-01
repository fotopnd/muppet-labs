import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useCases } from '@/api/cases'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Pagination } from '@/components/Pagination'
import { SeverityBadge } from '@/components/SeverityBadge'
import { StatusBadge } from '@/components/StatusBadge'
import type { CaseCategory, CaseFilters, CaseStatus, Severity } from '@/types'

const PAGE_SIZE = 50

export function CaseQueue() {
  const [page, setPage] = useState(1)
  const [category, setCategory] = useState<CaseCategory | ''>('')
  const [severity, setSeverity] = useState<Severity | ''>('')
  const [status, setStatus] = useState<CaseStatus | ''>('')

  const filters: CaseFilters = {
    page,
    page_size: PAGE_SIZE,
    ...(category && { category }),
    ...(severity && { severity }),
    ...(status && { status }),
  }

  const { data, isLoading, isError, error } = useCases(filters)

  function handleFilterChange(setter: (v: string) => void) {
    return (e: React.ChangeEvent<HTMLSelectElement>) => {
      setter(e.target.value)
      setPage(1)
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Case Queue</h1>
        <Link to="/audit" className="text-sm text-blue-600 hover:underline">
          Audit Log →
        </Link>
      </div>

      {/* Filters */}
      <div className="mb-4 flex flex-wrap gap-3">
        <select
          value={category}
          onChange={handleFilterChange(setCategory as (v: string) => void)}
          className="rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
          className="rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All severities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>

        <select
          value={status}
          onChange={handleFilterChange(setStatus as (v: string) => void)}
          className="rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="escalated">Escalated</option>
        </select>
      </div>

      {isError && (
        <ErrorMessage message={(error as Error).message ?? 'Failed to load cases'} />
      )}

      {isLoading && (
        <div className="py-12 text-center text-sm text-gray-500">Loading cases…</div>
      )}

      {data && (
        <>
          <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {['Case ID', 'Category', 'Severity', 'Status', 'Created'].map((h) => (
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
                      No cases match the current filters.
                    </td>
                  </tr>
                ) : (
                  data.items.map((c) => (
                    <tr key={c.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <Link
                          to={`/cases/${c.id}`}
                          className="font-mono text-sm text-blue-600 hover:underline"
                        >
                          {c.id.slice(0, 8)}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {c.category.replace('_', ' ')}
                      </td>
                      <td className="px-4 py-3">
                        <SeverityBadge severity={c.severity} />
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={c.status} />
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {new Date(c.created_at).toLocaleDateString()}
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
