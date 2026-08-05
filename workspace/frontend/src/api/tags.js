import { apiClient } from './client'

export async function fetchTags() {
  const { data } = await apiClient.get('/tags')
  return data
}

export async function assignTag(holdingId, name) {
  const { data } = await apiClient.post(`/portfolio/${holdingId}/tags`, { name })
  return data
}

export async function removeTag(holdingId, tagId) {
  const { data } = await apiClient.delete(`/portfolio/${holdingId}/tags/${tagId}`)
  return data
}
