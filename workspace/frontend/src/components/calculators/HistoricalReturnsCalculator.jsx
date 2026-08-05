import { useState } from 'react'
import { Button, showToast } from '../ui'
import { calcHistoricalReturns } from '../../api/calculators'
import { useHoldings } from '../../hooks/useHoldings'
import { formatCurrency, formatPercent, formatDate } from '../../utils/formatters'
import { getApiErrorMessage } from '../../utils/apiError'
import CalculatorResultSummary from './CalculatorResultSummary'

export default function HistoricalReturnsCalculator() {
  const { data: holdings = [] } = useHoldings()
  const [selectedAsset, setSelectedAsset] = useState(null)
  const [investDate, setInvestDate] = useState('')
  const [amount, setAmount] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [minDate, setMinDate] = useState(null)

  const assets = holdings.map((h) => ({ ...h.asset, holding_id: h.holding_id }))

  const handleAssetChange = (e) => {
    const assetId = parseInt(e.target.value)
    const asset = assets.find((a) => a.asset_id === assetId)
    setSelectedAsset(asset)
    setInvestDate('')
    setResult(null)
    // Min date would be the asset's earliest price_history — for now, just allow any date
    // A production impl would fetch price_history bounds from the asset detail
    setMinDate(null)
  }

  const handleCalculate = async () => {
    if (!selectedAsset || !investDate || !amount) {
      showToast.error('Please fill in all fields')
      return
    }

    setLoading(true)
    try {
      const data = await calcHistoricalReturns(selectedAsset.asset_id, investDate, amount)
      setResult(data)
    } catch (error) {
      showToast.error(getApiErrorMessage(error, 'Calculation failed'))
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setSelectedAsset(null)
    setInvestDate('')
    setAmount('')
    setResult(null)
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-2">Asset</label>
          <select
            value={selectedAsset?.asset_id || ''}
            onChange={handleAssetChange}
            className="w-full px-3 py-2 rounded border border-border bg-surface text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
          >
            <option value="">Select an asset</option>
            {assets.map((a) => (
              <option key={a.asset_id} value={a.asset_id}>
                {a.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-text-secondary mb-2">Invest Date</label>
          <input
            type="date"
            value={investDate}
            onChange={(e) => setInvestDate(e.target.value)}
            className="w-full px-3 py-2 rounded border border-border bg-surface text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-text-secondary mb-2">Amount (₹)</label>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="10000"
            className="w-full px-3 py-2 rounded border border-border bg-surface text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>
      </div>

      <div className="flex gap-2">
        <Button onClick={handleCalculate} disabled={loading}>
          {loading ? 'Calculating...' : 'Calculate'}
        </Button>
        {result && (
          <Button variant="ghost" onClick={handleReset}>
            Reset
          </Button>
        )}
      </div>

      {result && <CalculatorResultSummary data={result} type="historical-returns" />}
    </div>
  )
}
