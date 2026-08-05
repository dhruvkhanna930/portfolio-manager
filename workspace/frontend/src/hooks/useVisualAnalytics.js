/**
 * Hooks for the §15 visual layer's supporting reads.
 *
 * Kept separate from useAdvancedAnalytics (§14) so the phase boundary stays
 * legible -- these are presentation-support queries, not new analytics.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  createPriceTarget,
  deletePriceTarget,
  fetchAlerts,
  fetchPeerRank,
  fetchPortfolioSnapshot,
  fetchPriceTargets,
  fetchRiskReturn,
  fetchTimelineBounds,
} from '../api/analytics'

export function useRiskReturn(period = '1Y') {
  return useQuery({
    queryKey: ['analytics-risk-return', period],
    queryFn: () => fetchRiskReturn(period),
  })
}

export function useTimelineBounds() {
  return useQuery({
    queryKey: ['portfolio-timeline-bounds'],
    queryFn: fetchTimelineBounds,
    staleTime: 5 * 60 * 1000,
  })
}

export function usePortfolioSnapshot(onDate) {
  return useQuery({
    queryKey: ['portfolio-snapshot', onDate],
    queryFn: () => fetchPortfolioSnapshot(onDate),
    enabled: Boolean(onDate),
    // The scrubber revisits dates constantly; keeping them warm is what makes
    // dragging feel instant after the first pass.
    staleTime: 5 * 60 * 1000,
    placeholderData: (previous) => previous,
  })
}

export function usePeerRank(assetId, period = '1Y') {
  return useQuery({
    queryKey: ['asset-peer-rank', assetId, period],
    queryFn: () => fetchPeerRank(assetId, period),
    enabled: Boolean(assetId),
  })
}

export function useAlerts() {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: fetchAlerts,
    // §15.5: recomputed on read, so a short stale time is the whole "freshness"
    // story -- there is no push channel to invalidate from.
    staleTime: 60 * 1000,
  })
}

export function usePriceTargets() {
  return useQuery({ queryKey: ['price-targets'], queryFn: fetchPriceTargets })
}

export function useCreatePriceTarget() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createPriceTarget,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['price-targets'] })
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}

export function useDeletePriceTarget() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deletePriceTarget,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['price-targets'] })
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}
