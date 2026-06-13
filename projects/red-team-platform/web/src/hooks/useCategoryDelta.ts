import { useQuery } from '@tanstack/react-query'
import type { CategoryDeltaOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export function useCategoryDelta(model?: string | null) {
  const query = new URLSearchParams()
  if (model) query.set('model', model)

  return useQuery<CategoryDeltaOut>({
    queryKey: ['category-delta', model],
    queryFn: () => fetch(`${API}/regression/category-delta?${query}`).then((r) => r.json()),
    staleTime: 30_000,
  })
}
