import { apiClient } from './client'

export async function fetchAssets() {
  const { data } = await apiClient.get('/assets')
  return data
}

export async function searchLiveAssets(q, type) {
  const { data } = await apiClient.get('/assets/search/live', { params: { q, type } })
  return data
}

export async function resolveAsset({ symbol, asset_type, name }) {
  const { data } = await apiClient.post('/assets/resolve', { symbol, asset_type, name })
  return data
}
