import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { apiFetch } from '@/api/client'
import type { ReviewConfirmOut, ReviewSubmitBody, Session } from '@/types'

export function useSubmitReview(session: Session | undefined, nextSessionId: number | null) {
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (body: ReviewSubmitBody) =>
      apiFetch<ReviewConfirmOut>('/reviews', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      if (nextSessionId !== null) {
        navigate(`/review/${nextSessionId}`)
      } else if (session) {
        navigate(`/results/${session.experiment_id}`)
      }
    },
  })
}
