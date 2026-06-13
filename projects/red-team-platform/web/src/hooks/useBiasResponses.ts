import { useQuery } from '@tanstack/react-query'
import type { BiasTopicResponseOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export function useBiasResponses(topicId: string | null, model?: string | null) {
  const query = new URLSearchParams()
  if (model) query.set('model', model)

  return useQuery<BiasTopicResponseOut>({
    queryKey: ['bias-responses', topicId, model],
    queryFn: () => fetch(`${API}/bias/responses/${topicId}?${query}`).then((r) => r.json()),
    enabled: topicId !== null,
    staleTime: 60_000,
  })
}
