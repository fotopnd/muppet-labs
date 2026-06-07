import { useQuery } from '@tanstack/react-query'

import { apiFetch } from '@/api/client'
import type { Session } from '@/types'

export function useSession(id: number | null) {
  return useQuery({
    queryKey: ['session', id],
    queryFn: () => apiFetch<Session>(`/sessions/${id}`),
    enabled: id !== null,
    refetchInterval: false,
  })
}
