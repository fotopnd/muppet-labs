import { useQuery } from '@tanstack/react-query'
import type { AuditLogOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

type AuditLogParams = {
  decision?: string
  reviewer?: string
  limit?: number
  offset?: number
}

export function useAuditLog(params: AuditLogParams = {}) {
  const { decision, reviewer, limit = 50, offset = 0 } = params
  const query = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (decision) query.set('decision', decision)
  if (reviewer) query.set('reviewer', reviewer)

  return useQuery<AuditLogOut>({
    queryKey: ['audit-log', params],
    queryFn: () => fetch(`${API}/audit-log?${query}`).then((r) => r.json()),
    staleTime: 5_000,
  })
}
