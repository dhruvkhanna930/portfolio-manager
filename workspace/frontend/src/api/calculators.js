import { apiClient } from './client'

export async function calcHistoricalReturns(assetId, investDate, amount) {
  const { data } = await apiClient.post('/calculators/historical-returns', {
    asset_id: assetId,
    invest_date: investDate,
    amount,
  })
  return data
}

export async function calcSip(mode, payload) {
  const { data } = await apiClient.post('/calculators/sip', {
    mode,
    ...payload,
  })
  return data.data || data
}
