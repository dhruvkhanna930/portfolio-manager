import { apiClient } from './client'

export async function fetchWatchlist() {
  const { data } = await apiClient.get('/watchlist')
  return data
}

export async function addToWatchlist(assetId) {
  const { data } = await apiClient.post('/watchlist', { asset_id: assetId })
  return data
}

export async function removeFromWatchlist(assetId) {
  await apiClient.delete(`/watchlist/${assetId}`)
}
