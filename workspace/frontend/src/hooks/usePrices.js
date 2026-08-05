import { useMutation, useQueryClient } from '@tanstack/react-query'
import { syncPrices } from '../api/prices'

export function useSyncPrices() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: syncPrices,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['holdings'] }),
  })
}
