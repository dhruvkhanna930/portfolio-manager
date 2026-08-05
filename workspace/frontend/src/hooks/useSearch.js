import { useQuery } from '@tanstack/react-query'
import { searchOwnAssets } from '../api/search'

export function useOwnSearch(q) {
  return useQuery({
    queryKey: ['own-search', q],
    queryFn: () => searchOwnAssets(q),
    enabled: q.trim().length > 0,
    staleTime: 30_000,
  })
}
