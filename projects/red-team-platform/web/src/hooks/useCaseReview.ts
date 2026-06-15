import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { CaseReview } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export function useCaseReview(runId: string | null) {
  return useQuery<CaseReview | null>({
    queryKey: ['case-review', runId],
    queryFn: async () => {
      const res = await fetch(`${API}/runs/${runId}/review`)
      if (res.status === 404) return null
      if (!res.ok) throw new Error(`Failed to fetch review: ${res.status}`)
      return res.json() as Promise<CaseReview>
    },
    enabled: !!runId,
    staleTime: 5_000,
  })
}

type SubmitReviewPayload = {
  runId: string
  decision: 'approve' | 'flag' | 'escalate'
  reason: string | null
}

export function useSubmitReview() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: SubmitReviewPayload) => {
      const res = await fetch(`${API}/runs/${payload.runId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision: payload.decision,
          reason: payload.reason,
          reviewer: 'analyst-1',
        }),
      })
      if (!res.ok) throw new Error(`Failed to submit review: ${res.status}`)
      return res.json() as Promise<CaseReview>
    },
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: ['case-review', variables.runId] })
    },
  })
}
