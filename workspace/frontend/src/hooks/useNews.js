import { useQuery } from '@tanstack/react-query'
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
