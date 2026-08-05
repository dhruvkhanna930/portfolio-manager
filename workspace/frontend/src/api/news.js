import { apiClient } from './client'

export async function fetchGeneralNews(limit = 20, refresh = false) {
  const { data } = await apiClient.get('/news', { params: { limit, refresh } })
  return data
}

export async function fetchAssetNews(assetId, limit = 20, refresh = false) {
  const { data } = await apiClient.get('/news', {
    params: { asset_id: assetId, limit, refresh },
  })
  return data
}
