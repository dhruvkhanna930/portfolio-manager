import { apiClient } from './client'

export async function fetchAssets() {
  const { data } = await apiClient.get('/assets')
  return data
}
