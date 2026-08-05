import { useQuery } from '@tanstack/react-query'
import { fetchAllocation, fetchPortfolioPerformance, fetchPortfolioSummary } from '../api/analytics'

export function usePortfolioSummary() {
  return useQuery({ queryKey: ['portfolio-summary'], queryFn: fetchPortfolioSummary })
}

export function useAllocation(by) {
  return useQuery({ queryKey: ['portfolio-allocation', by], queryFn: () => fetchAllocation(by) })
}

export function usePortfolioPerformance(period) {
  return useQuery({
    queryKey: ['portfolio-performance', period],
    queryFn: () => fetchPortfolioPerformance(period),
  })
}
