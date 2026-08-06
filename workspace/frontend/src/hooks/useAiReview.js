import { useMutation, useQuery } from '@tanstack/react-query'

import { fetchAiStatus, generateAiReview } from '../api/analytics'

/** Whether the key is configured -- cheap, no model call, so a plain query. */
export function useAiStatus() {
  return useQuery({
    queryKey: ['ai', 'status'],
    queryFn: fetchAiStatus,
    staleTime: 10 * 60 * 1000,
  })
}

/**
 * Generation is a mutation, not a query: it spends a rate-limited external call,
 * so it must fire only when the user asks. A query here would regenerate on
 * remount and window focus and burn the free tier for nothing.
 */
export function useAiReview() {
  return useMutation({
    mutationFn: generateAiReview,
  })
}
