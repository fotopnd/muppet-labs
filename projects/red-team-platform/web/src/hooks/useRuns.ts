import { useQuery } from '@tanstack/react-query'
import type { RunListOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

type Params = {
  sessionId?: string | undefined
  page: number
  pageSize: number
  dedup?: boolean
}

export function useRuns(params: Params) {
  const { sessionId, page, pageSize, dedup } = params
  const query = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
    ...(sessionId ? { session_id: sessionId } : {}),
    ...(dedup ? { dedup: 'true' } : {}),
  })
  return useQuery<RunListOut>({
    queryKey: ['runs', params],
    queryFn: () => fetch(`${API}/runs?${query}`).then((r) => r.json()),
  })
}
