import { useQuery } from '@tanstack/react-query'

import { apiFetch } from '@/api/client'
import type { PapersPage } from '@/types'

export function usePapers(params?: { q?: string }) {
  const search = params?.q ? `?q=${encodeURIComponent(params.q)}` : ''
  return useQuery({
    queryKey: ['papers', params],
    queryFn: () => apiFetch<PapersPage>(`/papers${search}`),
  })
}
