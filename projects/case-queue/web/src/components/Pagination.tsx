interface PaginationProps {
  page: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
}

export function Pagination({ page, pageSize, total, onPageChange }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1
  const end = Math.min(page * pageSize, total)

  return (
    <div className="flex items-center justify-between px-1 py-3 text-sm text-gray-600">
      <span>
        {total === 0 ? 'No results' : `${start}–${end} of ${total}`}
      </span>
      <div className="flex gap-2">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="rounded border border-gray-300 px-3 py-1 disabled:opacity-40 hover:bg-gray-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        <span className="flex items-center px-1">
          {page} / {totalPages}
        </span>
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="rounded border border-gray-300 px-3 py-1 disabled:opacity-40 hover:bg-gray-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    </div>
  )
}
