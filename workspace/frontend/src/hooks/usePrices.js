import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchPrice, fetchPriceHistory, syncPrices } from '../api/prices'

export function useSyncPrices() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: syncPrices,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['holdings'] }),
  })
}

export function usePrice(assetId) {
  return useQuery({
    queryKey: ['price', assetId],
    queryFn: () => fetchPrice(assetId),
    enabled: Boolean(assetId),
    staleTime: 30_000,
  })
}

export function usePriceHistory(assetId, period) {
  return useQuery({
    queryKey: ['price-history', assetId, period],
    queryFn: () => fetchPriceHistory(assetId, period),
    enabled: Boolean(assetId),
  })
}
