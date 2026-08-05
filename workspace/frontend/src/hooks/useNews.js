import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchAssetNews, fetchGeneralNews } from '../api/news'

const GENERAL_NEWS_KEY = ['news', 'general']
const ASSET_NEWS_KEY = (assetId) => ['news', 'asset', assetId]

export function useGeneralNews(limit = 20) {
  return useQuery({
    queryKey: GENERAL_NEWS_KEY,
    queryFn: () => fetchGeneralNews(limit),
    staleTime: 1800_000, // 30 min
  })
}

export function useAssetNews(assetId, limit = 20) {
  return useQuery({
    queryKey: ASSET_NEWS_KEY(assetId),
    queryFn: () => fetchAssetNews(assetId, limit),
    staleTime: 1800_000,
  })
}

export function useRefreshGeneralNews(limit = 20) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => fetchGeneralNews(limit, true),
    onSuccess: (data) => queryClient.setQueryData(GENERAL_NEWS_KEY, data),
  })
}

export function useRefreshAssetNews(assetId, limit = 20) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => fetchAssetNews(assetId, limit, true),
    onSuccess: (data) => queryClient.setQueryData(ASSET_NEWS_KEY(assetId), data),
  })
}
