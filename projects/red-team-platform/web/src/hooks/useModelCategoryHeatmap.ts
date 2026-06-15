import { useQuery } from '@tanstack/react-query'
import type { ModelCategoryHeatmapOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export function useModelCategoryHeatmap() {
  return useQuery<ModelCategoryHeatmapOut>({
    queryKey: ['modelCategoryHeatmap'],
    queryFn: () => fetch(`${API}/model-category-heatmap`).then((r) => r.json()),
    refetchInterval: 30_000,
  })
}
