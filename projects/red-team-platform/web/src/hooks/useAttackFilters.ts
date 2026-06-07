import { useQuery } from '@tanstack/react-query'
import type { FilterValuesOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export function useHarmCategories() {
  return useQuery<FilterValuesOut>({
    queryKey: ['harmCategories'],
    queryFn: () => fetch(`${API}/attacks/harm-categories`).then((r) => r.json()),
  })
}

export function useStrategies() {
  return useQuery<FilterValuesOut>({
    queryKey: ['strategies'],
    queryFn: () => fetch(`${API}/attacks/strategies`).then((r) => r.json()),
  })
}
