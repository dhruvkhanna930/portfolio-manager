/**
 * Hooks for the Phase 16 recommendation model.
 *
 * Recommendations are expensive on the first call of a session (fundamentals
 * for the whole candidate universe get fetched and cached server-side), so the
 * stale time is generous -- rankings built on daily fundamentals have no reason
 * to be refetched on every tab switch.
 */

import { keepPreviousData, useQuery } from '@tanstack/react-query'

import {
  fetchAssetForecast,
  fetchRecommendationModelStatus,
  fetchRecommendations,
} from '../api/analytics'

const FIFTEEN_MINUTES = 15 * 60 * 1000

export function useRecommendations({ mode = 'similar', riskProfile = 'balanced', limit = 8, useMl = true } = {}) {
  return useQuery({
    queryKey: ['recommendations', mode, riskProfile, limit, useMl],
    queryFn: () => fetchRecommendations({ mode, riskProfile, limit, useMl }),
    staleTime: FIFTEEN_MINUTES,
    // Keeps the previous ranking on screen while a new mode loads, so switching
    // tabs doesn't blank the list out and reflow the page.
    placeholderData: keepPreviousData,
  })
}

export function useRecommendationModelStatus() {
  return useQuery({
    queryKey: ['recommendation-model-status'],
    queryFn: fetchRecommendationModelStatus,
    staleTime: FIFTEEN_MINUTES,
  })
}

export function useAssetForecast(assetId) {
  return useQuery({
    queryKey: ['asset-forecast', assetId],
    queryFn: () => fetchAssetForecast(assetId),
    enabled: Boolean(assetId),
    staleTime: FIFTEEN_MINUTES,
  })
}
