import { useQuery } from '@tanstack/react-query'
import { fetchMovers } from '../api/market'

export function useMovers(scope, limit = 5) {
  return useQuery({
    queryKey: ['market-movers', scope, limit],
    queryFn: () => fetchMovers(scope, limit),
    staleTime: 60_000,
  })
}
