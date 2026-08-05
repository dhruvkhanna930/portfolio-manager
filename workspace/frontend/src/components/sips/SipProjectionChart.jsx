import { useEffect, useState } from 'react'
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { calcSip } from '../../api/calculators'
import { formatCurrency } from '../../utils/formatters'
import Skeleton from '../ui/Skeleton'

// SIP frequency isn't always monthly, but the Phase 9 projection engine
// (sip_calc_projected) is a monthly-compounding model per CLAUDE.md §6.12 Mode A.
// Normalizing to an "effective monthly amount" lets every frequency reuse that
// same engine instead of building a second one just for non-monthly cadences.
const MONTHLY_EQUIVALENT = {
  DAILY: (amount) => amount * 30.44,
  WEEKLY: (amount) => amount * 4.345,
  MONTHLY: (amount) => amount * 1,
  QUARTERLY: (amount) => amount / 3,
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload
  return (
    <div className="rounded border border-border bg-surface px-3 py-2 text-sm shadow-lg">
      <p className="text-text-secondary">Year {point.year}</p>
      <p className="tabular-nums text-text-primary">
        Value: <span className="font-medium">{formatCurrency(point.value)}</span>
      </p>
      <p className="tabular-nums text-text-secondary">Invested: {formatCurrency(point.invested)}</p>
    </div>
  )
}

export default function SipProjectionChart({ sip, annualReturnPct, years, stepUpPct }) {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    const normalize = MONTHLY_EQUIVALENT[sip.frequency] ?? MONTHLY_EQUIVALENT.MONTHLY
    const monthlyAmount = normalize(Number(sip.amount))

    calcSip('projected', {
      monthly_amount: monthlyAmount,
      annual_return_pct: annualReturnPct,
      years,
      step_up_pct: stepUpPct || null,
    })
      .then((data) => {
        if (!cancelled) setResult(data)
      })
      .catch(() => {
        if (!cancelled) setError('Could not compute projection')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [sip.amount, sip.frequency, annualReturnPct, years, stepUpPct])

  if (loading) return <Skeleton className="h-48 w-full rounded" />
  if (error) return <p className="text-sm text-negative">{error}</p>
  if (!result || !result.yearly_breakdown?.length) return null

  const chartData = result.yearly_breakdown.map((p) => ({
    year: Number(p.year),
    value: Number(p.value),
    invested: Number(p.invested),
  }))

  return (
    <div>
      <div className="mb-3 grid grid-cols-3 gap-3 text-sm">
        <div>
          <p className="text-text-muted text-xs">Total Invested</p>
          <p className="tabular-nums font-medium text-text-primary">
            {formatCurrency(result.total_invested)}
          </p>
        </div>
        <div>
          <p className="text-text-muted text-xs">Projected Value</p>
          <p className="tabular-nums font-medium text-accent">{formatCurrency(result.final_value)}</p>
        </div>
        <div>
          <p className="text-text-muted text-xs">Return</p>
          <p
            className={`tabular-nums font-medium ${
              Number(result.total_return) >= 0 ? 'text-positive' : 'text-negative'
            }`}
          >
            {Number(result.total_return) >= 0 ? '+' : ''}
            {formatCurrency(result.total_return)} ({Number(result.total_return_pct).toFixed(1)}%)
          </p>
        </div>
      </div>

      <div className="h-48 w-full">
        <ResponsiveContainer>
          <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
            <defs>
              <linearGradient id={`sipFill-${sip.sip_id}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22D3A6" stopOpacity={0.28} />
                <stop offset="100%" stopColor="#22D3A6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="year"
              tickFormatter={(y) => `Y${y}`}
              stroke="#5C6270"
              tick={{ fontSize: 11, fill: '#9298A5' }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              domain={['auto', 'auto']}
              tickFormatter={(v) => formatCurrency(v, { compact: true })}
              stroke="#5C6270"
              tick={{ fontSize: 11, fill: '#9298A5' }}
              tickLine={false}
              axisLine={false}
              width={56}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#22D3A6"
              strokeWidth={2}
              fill={`url(#sipFill-${sip.sip_id})`}
              isAnimationActive
              animationDuration={250}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
