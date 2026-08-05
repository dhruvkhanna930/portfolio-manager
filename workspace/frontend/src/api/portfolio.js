import { apiClient } from './client'

export async function fetchHoldings() {
  const { data } = await apiClient.get('/portfolio')
  return data
}

export async function createHolding(payload) {
  const { data } = await apiClient.post('/portfolio', payload)
  return data
}

export async function updateHolding(holdingId, payload) {
  const { data } = await apiClient.put(`/portfolio/${holdingId}`, payload)
  return data
}

export async function deleteHolding(holdingId) {
  await apiClient.delete(`/portfolio/${holdingId}`)
}
