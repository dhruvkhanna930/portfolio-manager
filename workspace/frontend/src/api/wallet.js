import { apiClient } from './client'

export async function fetchWallet() {
  const { data } = await apiClient.get('/wallet')
  return data
}

export async function depositCash(amount) {
  const { data } = await apiClient.post('/wallet/deposit', { amount })
  return data
}

export async function withdrawCash(amount) {
  const { data } = await apiClient.post('/wallet/withdraw', { amount })
  return data
}
