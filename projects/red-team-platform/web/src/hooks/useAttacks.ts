import { useQuery } from '@tanstack/react-query'
import type { AttackListOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

type Params = {
  page: number
  pageSize: number
  source?: string
  harmCategory?: string
  strategy?: string
}

export function useAttacks(params: Params) {
  const { page, pageSize, source, harmCategory, strategy } = params
  const query = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
    ...(source ? { source } : {}),
    ...(harmCategory ? { harm_category: harmCategory } : {}),
    ...(strategy ? { strategy } : {}),
  })
  return useQuery<AttackListOut>({
    queryKey: ['attacks', params],
    queryFn: () => fetch(`${API}/attacks?${query}`).then((r) => r.json()),
  })
}
