import { apiClient } from './client'

export async function fetchMovers(scope = 'portfolio', limit = 5) {
  const { data } = await apiClient.get('/market/movers', { params: { scope, limit } })
  return data
}
