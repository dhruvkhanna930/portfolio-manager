import { apiClient } from './client'

export async function fetchPortfolioSummary() {
  const { data } = await apiClient.get('/portfolio/summary')
  return data
}

export async function fetchAllocation(by = 'type') {
  const { data } = await apiClient.get('/portfolio/allocation', { params: { by } })
  return data
}

export async function fetchPortfolioPerformance(period = '1Y') {
  const { data } = await apiClient.get('/portfolio/performance', { params: { period } })
  return data
}
