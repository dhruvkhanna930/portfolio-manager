import { apiClient } from './client'

export async function searchOwnAssets(q) {
  const { data } = await apiClient.get('/search', { params: { q } })
  return data
}
