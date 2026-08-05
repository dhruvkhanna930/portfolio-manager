import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  createGoal,
  deleteGoal,
  fetchBenchmark,
  fetchCorrelation,
  fetchGoals,
  fetchHealthScore,
  fetchMarketMood,
  fetchRisk,
  fetchStatistics,
  runMonteCarlo,
  runRebalancePreview,
} from '../api/analytics'

export function useRisk({ scope = 'portfolio', assetId, period = '1Y' } = {}) {
  return useQuery({
    queryKey: ['analytics-risk', scope, assetId ?? null, period],
    queryFn: () => fetchRisk({ scope, assetId, period }),
    // scope=asset without an asset_id is a 422 by design -- don't fire it.
    enabled: scope !== 'asset' || Boolean(assetId),
  })
}

export function useCorrelation(period = '1Y') {
  return useQuery({
    queryKey: ['analytics-correlation', period],
    queryFn: () => fetchCorrelation(period),
  })
}

export function useHealthScore(period = '1Y') {
  return useQuery({
    queryKey: ['analytics-health-score', period],
    queryFn: () => fetchHealthScore(period),
  })
}

export function useBenchmark({ codes = 'NIFTY50', period = '1Y', fdRatePct, inflationRatePct } = {}) {
  return useQuery({
    queryKey: ['analytics-benchmark', codes, period, fdRatePct ?? null, inflationRatePct ?? null],
    queryFn: () => fetchBenchmark({ codes, period, fdRatePct, inflationRatePct }),
  })
}

export function useStatistics() {
  return useQuery({ queryKey: ['analytics-statistics'], queryFn: fetchStatistics })
}

export function useMarketMood() {
  return useQuery({ queryKey: ['market-mood'], queryFn: fetchMarketMood })
}

// Monte Carlo and the rebalance preview are mutations rather than queries: both
// are POSTs the user triggers deliberately, and neither should re-run on window
// focus or cache-invalidation the way a query would.
export function useMonteCarlo() {
  return useMutation({ mutationFn: runMonteCarlo })
}

export function useRebalancePreview() {
  return useMutation({ mutationFn: runRebalancePreview })
}

export function useGoals() {
  return useQuery({ queryKey: ['goals'], queryFn: fetchGoals })
}

export function useCreateGoal() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createGoal,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['goals'] }),
  })
}

export function useDeleteGoal() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteGoal,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['goals'] }),
  })
}
