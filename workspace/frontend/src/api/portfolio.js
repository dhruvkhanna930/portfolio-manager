import { apiClient } from './client'

// v2: holdings are read-only -- they're derived from transactions. Creating,
// changing, or removing one happens through /api/transactions (BUY/SELL).
export async function fetchHoldings() {
  const { data } = await apiClient.get('/portfolio')
  return data
}
