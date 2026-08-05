import { useQuery } from '@tanstack/react-query'
import { fetchAllocation, fetchPortfolioSummary } from '../api/analytics'

export function usePortfolioSummary() {
  return useQuery({ queryKey: ['portfolio-summary'], queryFn: fetchPortfolioSummary })
}

export function useAllocation(by) {
  return useQuery({ queryKey: ['portfolio-allocation', by], queryFn: () => fetchAllocation(by) })
}
