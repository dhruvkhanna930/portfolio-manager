import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { deleteSip, fetchSips, updateSip } from '../api/sips'

const SIPS_KEY = ['sips']

export function useSips() {
  return useQuery({ queryKey: SIPS_KEY, queryFn: fetchSips })
}

export function useUpdateSip() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ sipId, payload }) => updateSip(sipId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: SIPS_KEY }),
  })
}

export function useDeleteSip() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (sipId) => deleteSip(sipId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: SIPS_KEY }),
  })
}
