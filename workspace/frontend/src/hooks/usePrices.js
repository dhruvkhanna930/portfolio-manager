import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchPriceHistory, syncPrices } from '../api/prices'

export function useSyncPrices() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: syncPrices,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['holdings'] }),
  })
}

export function usePriceHistory(assetId, period) {
  return useQuery({
    queryKey: ['price-history', assetId, period],
    queryFn: () => fetchPriceHistory(assetId, period),
    enabled: Boolean(assetId),
  })
}
