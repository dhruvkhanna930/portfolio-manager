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

// --- Phase 14: advanced analytics (CLAUDE.md §14.10) ---

export async function fetchRisk({ scope = 'portfolio', assetId, period = '1Y', benchmarkCode = 'NIFTY50' } = {}) {
  const params = { scope, period, benchmark_code: benchmarkCode }
  if (assetId) params.asset_id = assetId
  const { data } = await apiClient.get('/analytics/risk', { params })
  return data
}

export async function fetchCorrelation(period = '1Y') {
  const { data } = await apiClient.get('/analytics/correlation', { params: { period } })
  return data
}

export async function fetchHealthScore(period = '1Y') {
  const { data } = await apiClient.get('/analytics/health-score', { params: { period } })
  return data
}

export async function fetchBenchmark({ codes = 'NIFTY50', period = '1Y', fdRatePct, inflationRatePct } = {}) {
  const params = { codes, period }
  if (fdRatePct != null) params.fd_rate_pct = fdRatePct
  if (inflationRatePct != null) params.inflation_rate_pct = inflationRatePct
  const { data } = await apiClient.get('/analytics/benchmark', { params })
  return data
}

export async function fetchStatistics() {
  const { data } = await apiClient.get('/analytics/statistics')
  return data
}

export async function runMonteCarlo({ horizonDays = 252, nSimulations = 1000, period = 'ALL', seed } = {}) {
  const body = { horizon_days: horizonDays, n_simulations: nSimulations, period }
  if (seed != null) body.seed = seed
  const { data } = await apiClient.post('/analytics/monte-carlo', body)
  return data
}

export async function runRebalancePreview({ targetWeights, period = '1Y', benchmarkCode = 'NIFTY50' }) {
  const { data } = await apiClient.post('/analytics/rebalance-preview', {
    target_weights: targetWeights,
    period,
    benchmark_code: benchmarkCode,
  })
  return data
}

export async function fetchGoals() {
  const { data } = await apiClient.get('/goals')
  return data
}

export async function createGoal(payload) {
  const { data } = await apiClient.post('/goals', payload)
  return data
}

export async function deleteGoal(goalId) {
  await apiClient.delete(`/goals/${goalId}`)
  return goalId
}

export async function fetchMarketMood() {
  const { data } = await apiClient.get('/market/mood')
  return data
}

// --- Phase 15: supporting reads for the visual layer (CLAUDE.md §15) ---

export async function fetchRiskReturn(period = '1Y') {
  const { data } = await apiClient.get('/analytics/risk-return', { params: { period } })
  return data
}

export async function fetchPortfolioSnapshot(onDate) {
  const { data } = await apiClient.get('/portfolio/snapshot', { params: { on: onDate } })
  return data
}

export async function fetchTimelineBounds() {
  const { data } = await apiClient.get('/portfolio/timeline-bounds')
  return data
}

export async function fetchPeerRank(assetId, period = '1Y') {
  const { data } = await apiClient.get(`/assets/${assetId}/peer-rank`, { params: { period } })
  return data
}

export async function fetchAlerts() {
  const { data } = await apiClient.get('/alerts')
  return data
}

export async function fetchPriceTargets() {
  const { data } = await apiClient.get('/price-targets')
  return data
}

export async function createPriceTarget(payload) {
  const { data } = await apiClient.post('/price-targets', payload)
  return data
}

export async function deletePriceTarget(targetId) {
  await apiClient.delete(`/price-targets/${targetId}`)
  return targetId
}
