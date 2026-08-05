import { apiClient } from './client'

export async function fetchGeneralNews(limit = 20) {
  const { data } = await apiClient.get('/news', { params: { limit } })
  return data
}

export async function fetchAssetNews(assetId, limit = 20) {
  const { data } = await apiClient.get('/news', { params: { asset_id: assetId, limit } })
  return data
}
