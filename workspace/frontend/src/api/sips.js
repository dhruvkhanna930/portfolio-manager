import { apiClient } from './client'

export async function fetchSips() {
  const { data } = await apiClient.get('/sips')
  return data
}

export async function updateSip(sipId, payload) {
  const { data } = await apiClient.put(`/sips/${sipId}`, payload)
  return data
}

export async function deleteSip(sipId) {
  await apiClient.delete(`/sips/${sipId}`)
}
