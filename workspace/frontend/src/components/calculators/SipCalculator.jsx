import { useState } from 'react'
import { Button, showToast } from '../ui'
import { calcSip } from '../../api/calculators'
import { useHoldings } from '../../hooks/useHoldings'
import { getApiErrorMessage } from '../../utils/apiError'
import CalculatorResultSummary from './CalculatorResultSummary'

export default function SipCalculator() {
  const { data: holdings = [] } = useHoldings()
  const [mode, setMode] = useState('projected')
  const [monthlyAmount, setMonthlyAmount] = useState('')
  const [annualReturnPct, setAnnualReturnPct] = useState('12')
  const [years, setYears] = useState('10')
  const [selectedAsset, setSelectedAsset] = useState(null)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [stepUpPct, setStepUpPct] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const assets = holdings.map((h) => ({ ...h.asset, holding_id: h.holding_id }))

  const handleCalculate = async () => {
    if (!monthlyAmount) {
      showToast.error('Please enter a monthly amount')
      return
    }

    if (mode === 'projected' && (!annualReturnPct || !years)) {
      showToast.error('Please enter annual return % and years for projected mode')
      return
    }

    if (mode === 'historical' && (!selectedAsset || !startDate)) {
      showToast.error('Please select an asset and start date for historical mode')
      return
    }

    setLoading(true)
    try {
      const payload = {
        monthly_amount: parseFloat(monthlyAmount),
        step_up_pct: stepUpPct ? parseFloat(stepUpPct) : null,
      }

      if (mode === 'projected') {
        payload.annual_return_pct = parseFloat(annualReturnPct)
        payload.years = parseFloat(years)
      } else {
        payload.asset_id = selectedAsset.asset_id
        payload.start_date = startDate
        payload.end_date = endDate || null
      }

      const data = await calcSip(mode, payload)
      setResult(data)
    } catch (error) {
      showToast.error(getApiErrorMessage(error, 'Calculation failed'))
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setMonthlyAmount('')
    setAnnualReturnPct('12')
    setYears('10')
    setSelectedAsset(null)
    setStartDate('')
    setEndDate('')
    setStepUpPct('')
    setResult(null)
  }

  return (
    <div className="space-y-6">
      {/* Mode toggle */}
      <div>
        <p className="text-sm font-medium text-text-secondary mb-3">SIP Mode</p>
        <div className="flex gap-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              value="projected"
              checked={mode === 'projected'}
              onChange={(e) => {
                setMode(e.target.value)
                setResult(null)
              }}
            />
            <span className="text-sm">Projected (assumed return)</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              value="historical"
              checked={mode === 'historical'}
              onChange={(e) => {
                setMode(e.target.value)
                setResult(null)
              }}
            />
            <span className="text-sm">Historical (real price data)</span>
          </label>
        </div>
      </div>

      {/* Common fields */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-2">Monthly Amount (₹)</label>
          <input
            type="number"
            value={monthlyAmount}
            onChange={(e) => setMonthlyAmount(e.target.value)}
            placeholder="5000"
            className="w-full px-3 py-2 rounded border border-border bg-surface text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-text-secondary mb-2">
            Step-up per year (%) <span className="text-text-muted text-xs">(optional)</span>
          </label>
          <input
            type="number"
            value={stepUpPct}
            onChange={(e) => setStepUpPct(e.target.value)}
            placeholder="0"
            step="0.1"
            className="w-full px-3 py-2 rounded border border-border bg-surface text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>
      </div>

      {/* Mode-specific fields */}
      {mode === 'projected' ? (
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Expected Annual Return (%)
            </label>
            <input
              type="number"
              value={annualReturnPct}
              onChange={(e) => setAnnualReturnPct(e.target.value)}
              step="0.1"
              className="w-full px-3 py-2 rounded border border-border bg-surface text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">Duration (years)</label>
            <input
              type="number"
              value={years}
              onChange={(e) => setYears(e.target.value)}
              step="0.5"
              className="w-full px-3 py-2 rounded border border-border bg-surface text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">Asset</label>
            <select
              value={selectedAsset?.asset_id || ''}
              onChange={(e) => {
                const assetId = parseInt(e.target.value)
                setSelectedAsset(assets.find((a) => a.asset_id === assetId))
              }}
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
            <label className="block text-sm font-medium text-text-secondary mb-2">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 rounded border border-border bg-surface text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              End Date <span className="text-text-muted text-xs">(optional)</span>
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 rounded border border-border bg-surface text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
        </div>
      )}

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

      {result && <CalculatorResultSummary data={result} type="sip" mode={mode} />}
    </div>
  )
}
