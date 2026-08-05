import { useQuery } from '@tanstack/react-query'
import { fetchAssetDetail, fetchAssets, fetchSimilarAssets } from '../api/assets'

export function useAssets() {
  return useQuery({ queryKey: ['assets'], queryFn: fetchAssets })
}

export function useAssetDetail(assetId) {
  return useQuery({
    queryKey: ['asset-detail', assetId],
    queryFn: () => fetchAssetDetail(assetId),
    enabled: Boolean(assetId),
  })
}

export function useSimilarAssets(assetId) {
  return useQuery({
    queryKey: ['asset-similar', assetId],
    queryFn: () => fetchSimilarAssets(assetId),
    enabled: Boolean(assetId),
  })
}
