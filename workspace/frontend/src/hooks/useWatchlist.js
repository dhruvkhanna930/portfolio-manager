import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { addToWatchlist, fetchWatchlist, removeFromWatchlist } from '../api/watchlist'

const WATCHLIST_KEY = ['watchlist']

export function useWatchlist() {
  return useQuery({ queryKey: WATCHLIST_KEY, queryFn: fetchWatchlist })
}

export function useToggleWatchlist(assetId) {
  const queryClient = useQueryClient()
  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: WATCHLIST_KEY })
    queryClient.invalidateQueries({ queryKey: ['asset-detail', assetId] })
  }

  const add = useMutation({ mutationFn: () => addToWatchlist(assetId), onSuccess: invalidate })
  const remove = useMutation({ mutationFn: () => removeFromWatchlist(assetId), onSuccess: invalidate })

  return { add, remove }
}
