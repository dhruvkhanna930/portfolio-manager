import { apiClient } from './client'

export async function syncPrices() {
  const { data } = await apiClient.post('/prices/sync')
  return data
}

export async function fetchPrice(assetId) {
  const { data } = await apiClient.get(`/prices/${assetId}`)
  return data
}

export async function setManualPrice(assetId, price) {
  const { data } = await apiClient.put(`/prices/${assetId}/manual`, { price })
  return data
}
