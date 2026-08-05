import { apiClient } from './client'

export async function fetchTransactions() {
  const { data } = await apiClient.get('/transactions')
  return data
}

export async function createTransaction(payload) {
  const { data } = await apiClient.post('/transactions', payload)
  return data
}

export async function createSip(payload) {
  const { data } = await apiClient.post('/sips', payload)
  return data
}
