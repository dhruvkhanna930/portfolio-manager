import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createHolding, deleteHolding, fetchHoldings, updateHolding } from '../api/portfolio'

const HOLDINGS_KEY = ['holdings']

export function useHoldings() {
  return useQuery({ queryKey: HOLDINGS_KEY, queryFn: fetchHoldings })
}

export function useCreateHolding() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createHolding,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: HOLDINGS_KEY }),
  })
}

export function useUpdateHolding() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ holdingId, payload }) => updateHolding(holdingId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: HOLDINGS_KEY }),
  })
}

export function useDeleteHolding() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteHolding,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: HOLDINGS_KEY }),
  })
}
